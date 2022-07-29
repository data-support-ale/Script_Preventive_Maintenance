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
import syslog

syslog.openlog('support_switch_storm')
syslog.syslog(syslog.LOG_INFO, "Executing script")

from pattern import set_rule_pattern, set_portnumber, set_decision, get_decision, mysql_save

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

# Script init
script_name = sys.argv[0]

date = datetime.date.today()
date_hm = datetime.datetime.today()

pattern = sys.argv[1]
# pattern = 'slnHwlrnCbkHandler,and,port,and,bcmd'
print(pattern)
set_rule_pattern(pattern)

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
        print(msg)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog IP Address: " + ipadd)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog Hostname: " + host)
        #syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + msg)
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_storm.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_storm.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_storm.json - JSONDecodeError")
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
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_storm.json - JSONDecodeError")
        exit()
        
    if reason == "1":
        reason = "Broadcast"
    elif reason == "2":
        reason = "Multicast"
    elif reason == "3":
        reason = "Unknown unicast"

    set_portnumber(port)
    if alelog.rsyslog_script_timeout(ipadd + port + pattern, time.time()):
        syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
        print("Less than 5 min")
        exit(0)

syslog.syslog(syslog.LOG_INFO, "Executing function get_decision") 
decision = get_decision(ipadd)


if (len(decision) == 0) or (len(decision) == 1 and decision[0] == 'Yes'):
    syslog.syslog(syslog.LOG_INFO, "No Decision saved")
    answer = "0"
    syslog.syslog(syslog.LOG_INFO, "Executing function port_monitoring")
    port_monitoring(switch_user, switch_password, port, ipadd)
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_storm")
    filename_path, subject, action, result, category = collect_command_output_storm(switch_user, switch_password, port, reason, answer, host, ipadd)
    syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
    syslog.syslog(syslog.LOG_INFO, "Action: " + action)
    syslog.syslog(syslog.LOG_INFO, "Result: " + result)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
    send_file(filename_path, subject, action, result, category)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
    sleep(2)
    notif = ("A {0} Storm Threshold violation occurs on OmniSwitch {1} / {2} port {3}.\nDo you want to disable this port?\nThe port-monitoring capture of port {3} is available on Server directory /tftpboot/").format(reason,host,ipadd,port)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card " + notif)
    answer = send_message_request(notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
    print(answer)
    syslog.syslog(syslog.LOG_INFO, "Executing function set_decision: " + answer)
    set_decision(ipadd, answer)
    try:
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif + " Decision received: " + answer, exception='')
        syslog.syslog(syslog.LOG_INFO, "Statistics saved")    
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass
    #### Download port monitoring capture ###
    filename= '{0}_pmonitor_storm.enc'.format(host)
    remoteFilePath = '/flash/pmonitor.enc'
    localFilePath = "/tftpboot/{0}_{1}-{2}_{3}_{4}".format(date,date_hm.hour,date_hm.minute,ipadd,filename)
    try: 
       syslog.syslog(syslog.LOG_INFO, "Executing function get_file_sftp - remoteFilePath: " + remoteFilePath + " localFilePath: " + localFilePath) 
       get_file_sftp(switch_user, switch_password, ipadd, remoteFilePath, localFilePath)
    except:
        pass
elif 'No' in decision:
    syslog.syslog(syslog.LOG_INFO, "Decision saved to No - script exit")
    sys.exit()

elif 'yes and remember' in [d.lower() for d in decision]:
    answer = '2'
    syslog.syslog(syslog.LOG_INFO, "Decision saved to Yes and remember")

else:
    answer = '1'
    syslog.syslog(syslog.LOG_INFO, "No answer - Decision set to Yes") 

if answer == '1':
    syslog.syslog(syslog.LOG_INFO, "Decision set to Yes - Interface is administratively disabled and log collected")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_storm")
    filename_path, subject, action, result, category = collect_command_output_storm(switch_user, switch_password, port, reason, answer, host, ipadd)
    syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
    syslog.syslog(syslog.LOG_INFO, "Action: " + action)
    syslog.syslog(syslog.LOG_INFO, "Result: " + result)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
    send_file(filename_path, subject, action, result, category)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
    set_decision(ipadd, "4")
    try:
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')
        syslog.syslog(syslog.LOG_INFO, "Statistics saved")    
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 
elif answer == '2':
    syslog.syslog(syslog.LOG_INFO, "Decision set to Yes and remember - Interface is administratively disabled and log collected")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_storm")
    filename_path, subject, action, result, category = collect_command_output_storm(switch_user, switch_password, port, reason, answer, host, ipadd)
    syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
    syslog.syslog(syslog.LOG_INFO, "Action: " + action)
    syslog.syslog(syslog.LOG_INFO, "Result: " + result)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
    send_file(filename_path, subject, action, result, category)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
    set_decision(ipadd, "4")
    try:
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')
        syslog.syslog(syslog.LOG_INFO, "Statistics saved")    
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 
else:
    syslog.syslog(syslog.LOG_INFO, "No answer - Decision set to Yes - Script exit - will be called by next occurence")    
    sys.exit()

