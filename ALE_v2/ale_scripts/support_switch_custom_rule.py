#!/usr/bin/env python3

import sys
import os
import json
from support_tools_OmniSwitch import get_credentials, get_tech_support_sftp
from support_tools_Stellar import collect_logs
from support_send_notification import *
from time import strftime, localtime
import time

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
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company, room_id = get_credentials()

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
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_custom.json empty")
        exit()

set_portnumber("0")
set_decision(ipadd, "4")

if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
    print("Less than 5 min")
    exit(0)

if command in ["Send Notification", "Collect log and send notification"]:
    info = "The Custom Rule Pattern is deteched on device : {0} for Pattern : {1}".format(ipadd, pattern)
    send_message_detailed(info, jid1, jid2, jid3)
    
if command in ["Increase log verbosity", "Collect log and send notification"]:
    info = "Log of device : {0} for Pattern : {1}".format(ipadd, pattern)
    filename_path = "/var/log/devices/lastlog_custom.json"
    send_file_detailed(info, jid1, 'Custom Rule Triggered', 'Status: File sent', company, filename_path)
    
if command in ["Increase log verbosity", "Collect log and send notification"]:
    info = "Log of device : {0} for Pattern : {1}".format(ipadd, pattern)
    filename_path = "/var/log/devices/lastlog_custom.json"
    send_file_detailed(info, jid1, jid2, jid3, 'Custom Rule Triggered', 'Status: File sent', ipadd, company, filename_path)

if command in ["Collect log and send notification"]:
    set_decision(ipadd, "2")
    if ipadd == host:
        filename_path, subject, action, result, category = collect_logs(login_AP, pass_AP, ipadd, pattern)
        send_file_detailed(filename_path, subject, action, result, category)
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')

    else:
        ### TECH-SUPPORT ENG COMPLETE ###
        get_tech_support_sftp(switch_user, switch_password, host, ipadd)
        subject = ("Preventive Maintenance Application - The following pattern \"{0}\" is noticed on OmniSwitch {1}/{2}").format(pattern,host,ipadd)
        action = ("The following pattern \"{0}\" is noticed on OmniSwitch {1}/{2} - Tech-support eng complete is collected and stored in server {3}").format(pattern,host,ipadd,ip_server)
        result = "Please contact ALE Customer Support team for further troubleshooting"
        filename_path = "/var/log/devices/lastlog_custom.json"
        category = "custom_rule"
        send_file_detailed(filename_path, subject, action, result, category)
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')

mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=info, exception='')
os.system('logger -t montag -p user.info Process terminated')

# clear lastlog file
open('/var/log/devices/lastlog_custom.json', 'w').close()

sys.exit(0)
