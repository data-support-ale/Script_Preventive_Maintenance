#!/usr/local/bin/python3.7

import sys
import os
import json
from time import strftime, localtime
from support_tools_OmniSwitch import get_credentials
from support_send_notification import send_message, send_message_request, send_file
from database_conf import *
import re
import syslog

syslog.openlog('support_server_monitoring')
syslog.syslog(syslog.LOG_INFO, "Executing script")


runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

last = ""
with open("/var/log/devices/lastlog_server_monitoring.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_server_monitoring.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_server_monitoring.json", "r", errors='ignore') as log_file:
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
        print("File /var/log/devices/lastlog_server_monitoring.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_server_monitoring.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_server_monitoring.json - JSONDecodeError")
        exit()

# always 1
#never -1
# ? 0

# Sample log if TFTP Service does not start
# systemd[1]: Failed to start LSB: HPA's tftp server.
if "Failed to start LSB" in msg:
    try:
        pattern = "TFTP Service issue"
        syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
        notif = ("Preventive Maintenance Application - TFTP Service issue detected on Server server {0}.\nThis service is used for log collection of WLAN Stellar AP.\nDo you want to restart the TFTP Service?").format(ip_server)        #send_message(info, jid)
        syslog.syslog(syslog.LOG_INFO, "Notificattion: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
        answer = send_message_request(notif, jid)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except IndexError as error:
        print(error)
        sys.exit()
    sys.exit()
    # Sample log
    # qqchose
# Sample log for authentication failure
# {"@timestamp":"2022-07-01T13:12:07.633156+02:00","type":"syslog_json","relayip":"127.0.0.1","hostname":"debian2","message":"<38>Jul  1 13:12:07 sshd[48692]: Failed password for admin-support from 10.130.7.174 port 33196 ssh2","end_msg":""}
elif "Failed password" in msg:
    try:
        pattern = "SSH Authentication issue"
        login,user_ip,port,service = re.findall(r"Failed password for (.*?) from (.*?) port (.*?) (.*)", msg)[0]
        syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
        notif = ("Preventive Maintenance Application - SSH Authentication failure when connecting to server {0} .\n\nDetails: \n- User: {1}\n- IP Address: {2}.").format(ip_server,login,user_ip)      #send_message(info, jid)
        syslog.syslog(syslog.LOG_INFO, "Notificattion: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
        send_message(notif, jid)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except IndexError as error:
        print(error)
        sys.exit()
    sys.exit()
else:
    try:
        service_issue_reason = re.findall(r"Failed to start (.*)", msg)[0]
        notif = ("Preventive Maintenance Application - Service failure detected on server {0} .\n\nDetails: \n- Reason: {1}").format(ip_server,service_issue_reason)      #send_message(info, jid)
        syslog.syslog(syslog.LOG_INFO, "Notificattion: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send Notification")
        send_message(notif, jid)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
    except UnboundLocalError as error:
        print(error)
        syslog.syslog(syslog.LOG_INFO, "Regex does not match")
        sys.exit()
    except IndexError as error:
        print(error)
        syslog.syslog(syslog.LOG_INFO, "Regex does not match")
        sys.exit()
    sys.exit()
