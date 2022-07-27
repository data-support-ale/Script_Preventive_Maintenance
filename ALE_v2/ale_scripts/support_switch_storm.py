#!/usr/bin/env python3

import sys
import os
import re
import json
from support_tools_OmniSwitch import get_credentials, collect_command_output_storm, get_file_sftp, port_monitoring
from time import sleep
import datetime
from support_send_notification import *
import requests
import time

from pattern import set_rule_pattern, set_portnumber, set_decision, get_decision, mysql_save

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)

date = datetime.date.today()
date_hm = datetime.datetime.today()

pattern = sys.argv[1]
# pattern = 'slnHwlrnCbkHandler,and,port,and,bcmd'
print(pattern)
set_rule_pattern(pattern)
# info = ("We received following pattern from RSyslog {0}").format(pattern)
# os.system('logger -t montag -p user.info ' + info)

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company, room_id = get_credentials()


last = ""
with open("/var/log/devices/lastlog_storm.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_storm.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_storm.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_storm.json empty")
        exit()
    except IndexError:
        print("Index error in regex")
        exit()
 
 
    ## Sample Log
    ## swlogd intfCmm Mgr EVENT: CUSTLOG CMM Port 1\/1\/52 Storm Threshold violation - ingress traffic exceeds configured value 1
    ## On log if "ingress traffic exceeds configured value x" it does correspond to:
    ## Broadcast -  value 1
    ## Multicast - value 2
    ## Unknown unicast - value 3
    try:
        port, reason = re.findall(r"Port (.*?) Storm Threshold violation - ingress traffic exceeds configured value (.*)", msg)[0]
        port = port.replace("\'", "", 2)
    except IndexError:
        print("Index error in regex")
        exit()
        
    if reason == "1":
        reason = "Broadcast"
    elif reason == "2":
        reason = "Multicast"
    elif reason == "3":
        reason = "Unknown unicast"

    set_portnumber(port)
    if alelog.rsyslog_script_timeout(ipadd + port + pattern, time.time()):
        print("Less than 5 min")
        exit(0)

# always 1
#never -1
# ? 0
decision = get_decision(ipadd)
#save_resp = check_save(ipadd, port, "port_disable")


# if save_resp == "0":
if (len(decision) == 0) or (len(decision) == 1 and decision[0] == 'Yes'):
    answer = "0"
    port_monitoring(switch_user, switch_password, port, ipadd)
    filename_path, subject, action, result, category = collect_command_output_storm(switch_user, switch_password, port, reason, answer, host, ipadd)
    send_file(filename_path, subject, action, result, category)
    sleep(2)
    info = ("A {0} Storm Threshold violation occurs on OmniSwitch {1} / {2} port {3}.Do you want to disable this port?\nThe port-monitoring capture of port {3} is available on Server directory /tftpboot/").format(reason,host,ipadd,port)
    answer = send_message_request(info)
    print(answer)
    set_decision(ipadd, answer)
    mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=subject, exception='')
    #### Download port monitoring capture ###
    filename= '{0}_pmonitor_storm.enc'.format(host)
    remoteFilePath = '/flash/pmonitor.enc'
    localFilePath = "/tftpboot/{0}_{1}-{2}_{3}_{4}".format(date,date_hm.hour,date_hm.minute,ipadd,filename)
    try: 
       get_file_sftp(switch_user, switch_password, ipadd, remoteFilePath, localFilePath)
    except:
        pass
elif 'No' in decision:
    answer = "0"
    info = "Preventive Maintenance Application - A Storm Threshold violation has been detected on your network from the port {0} on device {1}.\nDecision saved for this switch/port is set to Never, we do not proceed further".format(port, ipadd, ip_server)
    send_message(info)
    sys.exit()

elif 'yes and remember' in [d.lower() for d in decision]:
    answer = '2'
#    info = ("Preventive Maintenance Application - A Storm Threshold violation has been detected on your network from the port {0} on device {1}.Decision saved for this switch/port is set to Always, we do proceed for disabling the interface").format(port, ipadd, ip_server)
#    print(info)
#    send_message(info)
else:
    answer = '1'

if answer == '1':
    os.system('logger -t montag -p user.info Process terminated')
    filename_path, subject, action, result, category = collect_command_output_storm(switch_user, switch_password, port, reason, answer, host, ipadd)
    send_file(filename_path, subject, action, result, category)
    mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')
elif answer == '2':
    info = ("Preventive Maintenance Application - A Storm Threshold violation has been detected on your network from the port {0} on device {1}.Decision saved for this switch/port is set to Always, we do proceed for disabling the interface").format(port, ipadd, ip_server)
    send_message(info)
    mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=info, exception='')
    os.system('logger -t montag -p user.info Process terminated')
    cmd = "clear violation port " + port
    os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user, ipadd, cmd))
else:
    info = ("Preventive Maintenance Application - A Storm Threshold violation has been detected on your network from the port {0} on device {1}.\nDecision saved for this switch/port is set to Never, we do not proceed further.").format(port,ipadd,ip_server)
    mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=info, exception='')
    print("Mail request set as no")
    os.system('logger -t montag -p user.info Mail request set as no')
    sleep(1)
