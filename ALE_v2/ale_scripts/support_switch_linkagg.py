#!/usr/bin/env python3

import sys
import os
import re
import json
from support_tools_OmniSwitch import collect_command_output_linkagg, get_credentials, get_file_sftp, port_monitoring, collect_command_output_lldp_port_description, ssh_connectivity_check, get_arp_entry
from time import strftime, localtime, sleep
import datetime
from support_send_notification import *
# from database_conf import *
import requests
import time

from pattern import set_rule_pattern, set_portnumber, set_decision, get_decision, mysql_save

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)

pattern = sys.argv[1]
print(pattern)
set_rule_pattern(pattern)
# info = ("We received following pattern from RSyslog {0}").format(pattern)
# os.system('logger -t montag -p user.info ' + info)

# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company, room_id = get_credentials()

date = datetime.date.today()
date_hm = datetime.datetime.today()

last = ""
with open("/var/log/devices/lastlog_linkagg.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_linkagg.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_linkagg.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ip = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_linkagg.json empty")
        exit()
    except IndexError:
        print("Index error in regex")
        exit()
 
    ## Sample Log
    ## OS6860E_VC_Core swlogd linkAggCmm main INFO: Receive agg port leave request: agg: 1, port: 1/1/1(0)
    os.system('logger -t montag -p user.info Executing script support_switch_linkagg - start')
    try:
        agg, port = re.findall(r"Receive agg port leave request: agg: (.*?), port:(.*?)\(", msg)[0]
        print(port)
    except IndexError:
        print("Index error in regex")
        os.system('logger -t montag -p user.info Executing script support_switch_linkagg - Index error in regex')
        exit()

    set_portnumber(port)
    if alelog.rsyslog_script_timeout(ip + port + pattern, time.time()):
        print("Less than 5 min")
        exit(0)
        
# always 1
#never -1
# ? 0
# save_resp = check_save(ip,agg, "linkagg")
decision = get_decision(ip)


# if save_resp == "0":
if (len(decision) == 0) or (len(decision) == 1 and decision[0] == 'Yes'):
    port_monitoring(switch_user, switch_password, port, ip)
    notif = "A LinkAgg Port Leave occurs on OmniSwitch " + host + " port " + port + " LinkAgg " + agg
    # send_message(notif, jid)
    send_message(notif)
    lldp_port_description, lldp_mac_address = collect_command_output_lldp_port_description(switch_user, switch_password, port, ip)  
    if lldp_port_description == 0:
        set_decision(ip, "4")
        device_type = answer = 0
        filename_path, subject, action, result, category = collect_command_output_linkagg(switch_user, switch_password, agg, host, ip)
        send_file(filename_path, subject, action, result, category) 
        mysql_save(runtime=_runtime, ip_address=ip, result='success', reason=action, exception='')
    elif "OAW-AP" in str(lldp_port_description):
        # If LLDP Remote System is Stellar AP we search for IP Address in ARP Table
        device_ip = get_arp_entry(switch_user, switch_password, lldp_mac_address, ip)
        device_type = "OAW-AP"
        notif = "A LinkAgg Port Leave occurs on OmniSwitch " + host + " port " + port + " LinkAgg " + agg + " - Port Description: " + lldp_port_description + ". Stellar AP " + device_ip + "/" + lldp_mac_address + " is connected to this port, do you want to collect AP logs? The port-monitoring capture of port " + port + " is available on Server " + ip_server + " directory /tftpboot/"
        # If LLDP Remote System is Stellar AP we propose to collect AP Logs
        # answer = send_message_request(notif, jid)
        answer = send_message_request(notif)
        print(answer)      
        mysql_save(runtime=_runtime, ip_address=ip, result='success', reason=notif, exception='')
    
    else:
        set_decision(ip, "4")
        device_type = "Others"
        filename_path, subject, action, result, category = collect_command_output_linkagg(switch_user, switch_password, agg, host, ip)
        action = "A LinkAgg Port Leave occurs on OmniSwitch " + host + " port " + port + " LinkAgg " + agg + " - Port Description: " + lldp_port_description + ". The port-monitoring capture of port " + port + " is available on Server " + ip_server + " directory /tftpboot/"
        send_file(filename_path, subject, action, result, category) 
        mysql_save(runtime=_runtime, ip_address=ip, result='success', reason=action, exception='')
    sleep(2)
    #### Download port monitoring capture ###
    filename= '{0}_pmonitor_linkagg.enc'.format(host)
    remoteFilePath = '/flash/pmonitor.enc'
    localFilePath = "/tftpboot/{0}_{1}-{2}_{3}_{4}".format(date,date_hm.hour,date_hm.minute,ip,filename)
    try: 
       get_file_sftp(switch_user, switch_password, ip, remoteFilePath, localFilePath)
    except:
        pass
    # if answer == "2":
    #     add_new_save(ip,port, "linkagg", choice="always")
    # elif answer == "0":
    #     add_new_save(ip,port, "linkagg", choice="never")
    # else:
    #     pass

    notif = "Preventive Maintenance Application - LinkAgg issue detected on OmniSwitch " + host + ". Do you want to keep being notified? " + ip_server        #send_message(info, jid)
    # answer = send_message_request(notif, jid)
    answer = send_message_request(notif)
    print(answer)
    set_decision(ip, answer)
    # if answer == "2":
    #     add_new_save(ip, agg, "linkagg", choice="always")
    # elif answer == "0":
    #     add_new_save(ip, agg, "linkagg", choice="never")

# elif save_resp == "-1":
elif 'No' in decision:
    #info = "A LinkAgg Port Leave has been detected on your network from the port {0}/Agg {1} on device {2}. Decision saved for this switch/port is set to Never, we do not proceed further".format(port, agg, ip)
    #send_message(info,jid)
    print("Decision set to never - exit")
    try:
        print(port)
        print(agg)
        print(ip)
        sys.exit()   
    except UnboundLocalError as error:
       print(error)
       sys.exit()
    except Exception as error:
       print(error)
       sys.exit() 

# elif save_resp == "1":
elif 'yes and remember' in [d.lower() for d in decision]:
    answer = '2'
    info = "A LinkAgg Port Leave has been detected on your network from the port {0} on device {1}. Decision saved for this switch/port is set to Always, we do proceed for disabling the interface".format(port, ip, ip_server)
    # send_message(info,jid)
    send_message(info)
else:
    info = "A LinkAgg Port Leave has been detected on your network from the port {0} on device {1}. Decision saved for this switch/port is set to Always, we do proceed for disabling the interface".format(port, ip, ip_server)
    # send_message(info,jid)
    send_message(info)

if answer == '1':
    if device_type == "OAW-AP":
        os.system('logger -t montag -p user.info Collecting Snapshot logs on Stellar AP')
        cmd = "sudo tech_support_command 12 " + ip_server
        ssh_connectivity_check(login_AP, pass_AP, device_ip, cmd)
        os.system('logger -t montag -p user.info Collecting logs on OmniSwitch')
        filename_path, subject, action, result, category = collect_command_output_linkagg(switch_user, switch_password, agg, host, ip)
        send_file(filename_path, subject, action, result, category)
    else:
        os.system('logger -t montag -p user.info Collecting logs on OmniSwitch')
        filename_path, subject, action, result, category = collect_command_output_linkagg(switch_user, switch_password, agg, host, ip)
        send_file(filename_path, subject, action, result, category)

elif answer == '2':
    os.system('logger -t montag -p user.info Process terminated')
    cmd = "clear violation port " + port
    os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
        switch_password, switch_user, ip, cmd))

else:
    print("Mail request set as no")
    os.system('logger -t montag -p user.info Mail request set as no')
    sleep(1)
