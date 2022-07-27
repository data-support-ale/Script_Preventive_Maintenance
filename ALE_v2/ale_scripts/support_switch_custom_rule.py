#!/usr/bin/env python3

import sys
import os
import json
from support_tools_OmniSwitch import get_credentials, get_tech_support_sftp
from support_tools_Stellar import collect_logs
from support_send_notification import *
from time import strftime, localtime
import time
import syslog

syslog.openlog('support_switch_custom_rule')
syslog.syslog(syslog.LOG_INFO, "Executing script")

from pattern import set_rule_pattern, set_portnumber, set_decision, get_decision, mysql_save

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)

command = sys.argv[1]
pattern = sys.argv[2]
set_rule_pattern(pattern)

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
print(sys.executable)

# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company, room_id = get_credentials()

last = ""
with open("/var/log/devices/lastlog_custom.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_custom.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_custom.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        print(log_json)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog IP Address: " + ipadd)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog Hostname: " + host)
        #syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + msg)
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_bgp.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_bgp.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_bgp.json - Index error in regex")
        exit()

set_portnumber("0")
set_decision(ipadd, "4")

if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
    print("Less than 5 min")
    syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval")
    exit(0)

if command in ["Send Notification", "Collect log and send notification"]:
    notif = "The Custom Rule Pattern is detected on device : {0} for Pattern : {1}".format(ipadd, pattern)
    syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
    syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Send notification")
    send_message(notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
    mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
    syslog.syslog(syslog.LOG_INFO, "Statistics saved")

if command in ["Increase log verbosity", "Collect log and send notification"]:
    notif = "Log of device : {0} for Pattern : {1}".format(ipadd, pattern)
    filename_path = "/var/log/devices/lastlog_custom.json"
    syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
    syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Send notification")
    send_file(filename_path, 'Custom Rule Triggered', notif, 'Status: File sent', category)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
    mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
    syslog.syslog(syslog.LOG_INFO, "Statistics saved")

if command in ["Increase log verbosity", "Collect log and send notification"]:
    notif = "Log of device : {0} for Pattern : {1}".format(ipadd, pattern)
    filename_path = "/var/log/devices/lastlog_custom.json"
    syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
    syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Send notification")
    send_file(filename_path, 'Custom Rule Triggered', notif, 'Status: File sent', category)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
    mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
    syslog.syslog(syslog.LOG_INFO, "Statistics saved")

if command in ["Collect log and send notification"]:
    if ipadd == host:
        syslog.syslog(syslog.LOG_INFO, "Device is a Stellar WLAN AP")
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Executing function collect_logs")
        filename_path, subject, action, result, category = collect_logs(login_AP, pass_AP, ipadd, pattern)
        syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Send notification")
        send_file(filename_path, subject, action, result, category)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')
        syslog.syslog(syslog.LOG_INFO, "Statistics saved")

    else:
        ### TECH-SUPPORT ENG COMPLETE ###
        syslog.syslog(syslog.LOG_INFO, "Executing function get_tech_support_sftp")
        get_tech_support_sftp(switch_user, switch_password, host, ipadd)
        subject = ("Preventive Maintenance Application - The following pattern \"{0}\" is noticed on OmniSwitch {1}/{2}").format(pattern,host,ipadd)
        action = ("The following pattern \"{0}\" is noticed on OmniSwitch {1}/{2} - Tech-support eng complete is collected and stored in server {3}").format(pattern,host,ipadd,ip_server)
        result = "Please contact ALE Customer Support team for further troubleshooting"
        filename_path = "/var/log/devices/lastlog_custom.json"
        category = "custom_rule"
        syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
        syslog.syslog(syslog.LOG_INFO, "Action: " + action)
        syslog.syslog(syslog.LOG_INFO, "Result: " + result)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API")
        send_file(filename_path, subject, action, result, category)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')
        syslog.syslog(syslog.LOG_INFO, "Statistics saved")

# clear lastlog file
open('/var/log/devices/lastlog_custom.json', 'w').close()

