#!/usr/local/bin/python3.7

import os
import json
import logging
import sys
from time import gmtime, strftime, localtime
from support_tools_OmniSwitch import get_credentials
from support_tools_Stellar import collect_logs
from support_send_notification import *
import syslog

syslog.openlog('support_wlan_get_log')
runtime = strftime("%d_%b_%Y_%H_%M_%S_0000", localtime())
uname = os.system('uname -a')
system_name = os.uname()[1].replace(" ", "_")
logging.info("Running on {0} at {1} ".format(system_name, runtime))

pattern = sys.argv[1]
print(pattern)

switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()
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
        print(msg)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog IP Address: " + ipadd)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog Hostname: " + host)
        #syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + msg)
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/get_log_ap.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/get_log_ap.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/get_log_ap.json - Index error in regex")
        exit()

syslog.syslog(syslog.LOG_INFO, "Executing function collect_logs")
filename_path, subject, action, result, category = collect_logs(login_AP, pass_AP, ipadd, pattern)
syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
syslog.syslog(syslog.LOG_INFO, "Action: " + action)
syslog.syslog(syslog.LOG_INFO, "Result: " + result)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")            
send_file_detailed(filename_path, subject, action, result, category)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

# clear log file
open('/var/log/devices/get_log_ap.json', 'w').close()