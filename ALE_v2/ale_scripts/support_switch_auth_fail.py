#!/usr/bin/env python3

from ipaddress import ip_address
import sys
import os
import re
import json
import syslog
from support_tools_OmniSwitch import get_credentials
from time import strftime, localtime, sleep
from support_send_notification import *
#from database_conf import *
import time
import syslog

syslog.openlog('support_switch_auth_fail')
syslog.syslog(syslog.LOG_INFO, "Executing script")

from pattern import set_rule_pattern, set_portnumber, set_decision, mysql_save

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

script_name = sys.argv[0]

pattern = sys.argv[1]
print(pattern)
set_rule_pattern(pattern)
# info = ("We received following pattern from RSyslog {0}").format(pattern)
# os.system('logger -t montag -p user.info ' + info)

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company, room_id = get_credentials()

last = ""
with open("/var/log/devices/lastlog_authfail.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_authfail.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_authfail.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd= log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
        print(msg)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog IP Address: " + ipadd)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog Hostname: " + host)
        #syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + msg)
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
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_authfail.json - Index error in regex")
        exit()

set_portnumber("0")
if alelog.rsyslog_script_timeout(ipadd+ "0" + pattern, time.time()):
    print("Less than 5 min")
    syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
    exit(0)


#notif = "Authentication failed on OmniSwitch \"" + host + "\" IP: " + ipadd+ " user login: " + user + " from source IP Address: " + source_ipadd+ " protocol: " + protocol
notif = "Preventive Maintenance Application - Authentication failed on OmniSwitch {0} / {1}\n\nDetails:\n- User Login : {2}\n- Source IP Address : {3}\n- Protocol : {4}\n".format(host, ipadd, user, source_ip, protocol)
syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
send_message(notif)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
set_decision(ipadd, "4")
try:
    mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
    syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision")    
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass   
