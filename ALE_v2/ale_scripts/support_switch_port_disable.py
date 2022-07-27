#!/usr/bin/env python3

from http.client import OK
import sys
import os
from support_tools_OmniSwitch import get_credentials, detect_port_loop, ssh_connectivity_check, debugging, collect_command_output_network_loop
from time import strftime, localtime, sleep
import re  # Regex
from support_send_notification import *
from database_conf import *
import time

from pattern import set_rule_pattern, set_portnumber, set_decision, get_decision, mysql_save

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)

pattern = sys.argv[1]
# pattern = 'slnHwlrnCbkHandler,and,port,and,bcmd'
print(pattern)
set_rule_pattern(pattern)
# info = ("We received following pattern from RSyslog {0}").format(pattern)
# os.system('logger -t montag -p user.info ' + info)

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company, room_id = get_credentials()

#### New rules to be added in the Rsyslog.conf ####
#if $msg contains 'slNi MACMOVE' and $msg contains 'macCallBackProcessing' then {
#     $RepeatedMsgReduction on
#     action(type="omfile" DynaFile="deviceloghistory" template="json_syslog" DirCreateMode="0755" FileCreateMode="0755")
#     action(type="omfile" DynaFile="devicelogloop" template="json_syslog" DirCreateMode="0755" FileCreateMode="0755")
#     action(type="omprog" name="support_lan_generic_loop" binary="/opt/ALE_Script/support_switch_port_disable.py" queue.type="LinkedList" queue.size="1" queue.workerThreads="1" queue.discardMark="20")
#     stop
#}

content_variable = open('/var/log/devices/lastlog_loop.json', 'r')
file_lines = content_variable.readlines()
content_variable.close()


if len(file_lines) != 0:
    last_line = file_lines[0]
    f = last_line.split(',')
    # For each element, look if relayip is present. If yes,  separate the text and the ip address
    for element in f:
        if "relayip" in element:
            element_split = element.split(':')
            ipadd_quot = element_split[1]
            # delete quotations
            ipadd = ipadd_quot[-len(ipadd_quot)+1:-1]
            print(ipadd)
            port = 0
            slot = 0
          # For each element, look if c/s/p is present. If yes,  we take the next element which is the port number
          # Log format OS6860E-VC-Building6 swlogd slNi MACMOVE DBG2: macCallBackProcessing_t[1174] [u:0][INS]: c/s/p: 1/1/14  d:vlan(1) MAC: 00:80:9f:57:df:33 vid:68 p:13 b:bridging t:learned e:0 dup:0 L3:0 cpu:0 mbi:0 McEntryNew:
        if " c\/s\/p:" in element:
            element_split = element.split()
            print(element_split)
            for i in range(len(element_split)):
                if element_split[i] == "c\\/s\\/p:":
                    port_a = element_split[i+1]
                    port = port_a.replace("\\", "", 2)
                    print(port)
                    set_portnumber(port)
    open('/var/log/devices/lastlog_loop.json', 'w').close()

    if alelog.rsyslog_script_timeout(ipadd + str(port) + pattern, time.time()):
        print("Less than 5 min")
        open('/var/log/devices/lastlog_loop.json', 'w').close()
        exit(0)

# if check_timestamp()>15: # if the last log has been received less than 10 seconds ago :
if detect_port_loop():  # if there is more than 10 log with less of 2 seconds apart:
    print("call function disable port")
    subject = "A loop was detected on your OmniSwitch!"

    decision = get_decision(ipadd)
    answer = "1"
    if (len(decision) == 0) or (len(decision) == 1 and decision[0] == 'Yes'):
        info = "A loop has been detected on your network from the port {0} on device {1}.\nIf you click on Yes, the following action will be done: Port Admin Down".format(port, ipadd)
        answer = send_message_request_detailed(info, jid1, jid2, jid3)

        set_decision(ipadd, answer)
    elif 'No' in decision: 
        # Disable debugging logs "swlog appid slNi subapp 20 level debug2"
        info = "Preventive Maintenance Application - A loop has been detected on your network from the port {0} on device {1}.\nDecision saved for this switch/port is set to Never, we do not proceed further".format(port, ipadd, ip_server)
        send_message_detailed(info, jid1, jid2, jid3)


        appid = "slNi"
        subapp = "all"
        level = "info"
        # Call debugging function from support_tools_OmniSwitch
        print("call function enable debugging")
        debugging(switch_user, switch_password, ipadd, appid, subapp, level)
    elif 'yes and remember' in [d.lower() for d in decision]:
        answer = '1'
    else:
        answer = '1'
        
    if answer == '1' or answer == '2':
        l_switch_cmd = []
        cmd = "interfaces port {0} admin-state disable".format(port)
        os.system('logger -t montag -p user.info Calling ssh_connectivity_check script')
        os.system('logger -t montag -p user.info SSH session for disabling port')
        ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)

        os.system('logger -t montag -p user.info Port disabled')
        filename_path, subject, action, result, category = collect_command_output_network_loop(switch_user, switch_password, ipadd, port)
        send_file_detailed(subject, jid1, action, result, company, filename_path)
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='') 
        sleep(5)
        # Disable debugging logs "swlog appid slNi subapp all level info"
        appid = "slNi"
        subapp = "all"
        level = "info"
        # Call debugging function from support_tools_OmniSwitch
        print("call function enable debugging")
        os.system('logger -t montag -p user.info SSH session for disabling logs')
        debugging(switch_user, switch_password, ipadd, appid, subapp, level)
        # clear lastlog file
        sleep(10)
        open('/var/log/devices/lastlog_loop.json', 'w').close()
    else:
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason="No action done", exception='')
        print("Mail request set as no")
        os.system('logger -t montag -p user.info Mail request set as no')
        sleep(1)
        open('/var/log/devices/lastlog_loop.json', 'w').close()

else:
    print("logs are too close")
    os.system('logger -t montag -p user.info Logs are too close')
    # clear lastlog file
    open('/var/log/devices/lastlog_loop.json', 'w').close()
