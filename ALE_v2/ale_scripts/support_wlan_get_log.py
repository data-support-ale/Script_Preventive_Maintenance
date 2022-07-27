#!/usr/bin/env python3

import sys
import os
import getopt
import re
import json
import logging
import subprocess
from time import gmtime, strftime, localtime
from support_tools_OmniSwitch import get_credentials
from support_tools_Stellar import collect_logs
from support_send_notification import *
import time
import syslog

from pattern import set_rule_pattern, set_portnumber, set_decision, mysql_save

syslog.openlog('support_wlan_get_log')

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

_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

runtime = strftime("%d_%b_%Y_%H_%M_%S_0000", localtime())
uname = os.system('uname -a')
system_name = os.uname()[1].replace(" ", "_")

switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company, room_id = get_credentials()
last = ""
with open("/var/log/devices/get_log_ap.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/get_log_ap.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/get_log_ap.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("/var/log/devices/get_log_ap.json empty")
        exit()

set_portnumber("0")
set_decision(ipadd, "4")
if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
    print("Less than 5 min")
    exit(0)

syslog.syslog(syslog.LOG_INFO, "Executing function collect_logs")
filename_path, subject, action, result, category = collect_logs(login_AP, pass_AP, ipadd, pattern)
syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
syslog.syslog(syslog.LOG_INFO, "Action: " + action)
syslog.syslog(syslog.LOG_INFO, "Result: " + result)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")            
send_file(filename_path, subject, action, result, category)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")


# clear log file
open('/var/log/devices/get_log_ap.json', 'w').close()
