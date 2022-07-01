#!/usr/local/bin/python3.7

import sys
import os
import re
import json
from support_tools_OmniSwitch import get_credentials
from time import strftime, localtime, sleep
from support_send_notification import send_message
from database_conf import *
import sys
import syslog

syslog.openlog('support_switch_auth_fail')
syslog.syslog(syslog.LOG_INFO, "Executing script")


runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

last = ""
with open("/var/log/devices/lastlog_authfail.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_authfail.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_authfail.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
        print(msg)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog IP Address: " + ipadd)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog Hostname: " + host)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + msg)
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_authfail.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_authfail.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_authfail.json - Index error in regex")
        exit()
    try:
        user, source_ip, protocol = re.findall(r"Login by (.*?) from (.*?) through (.*?) Failed", msg)[0]
    except IndexError:
        print("Index error in regex")
        exit()

notif = "Preventive Maintenance Application - Authentication failed on OmniSwitch {0} / {1}\n\nDetails:\n- User Login : {2}\n- Source IP Address : {3}\n- Protocol : {4}\n".format(host, ipadd, user, source_ip, protocol)
syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send Notification")
send_message(notif, jid)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

sleep(1)
open('/var/log/devices/lastlog_authfail.json', 'w').close()

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"user": user, "IP": ip, "protocol": protocol, "source_ip": source_ip}, "fields": {"count": 1}}])
    syslog.syslog(syslog.LOG_INFO, "Statistics saved")
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass
