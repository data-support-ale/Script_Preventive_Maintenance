#!/usr/bin/env python3

import sys
import os
import json
import re
import syslog
from support_tools_OmniSwitch import get_credentials, debugging
from time import strftime, localtime
from support_send_notification import *
# from database_conf import *
import time
import syslog

syslog.openlog('support_switch_debugging_ddos')
syslog.syslog(syslog.LOG_INFO, "Executing script")


from pattern import set_rule_pattern, set_portnumber, set_decision, mysql_save

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

# Script init
script_name = sys.argv[0]

pattern = sys.argv[1]
print(pattern)
set_rule_pattern(pattern)
# info = ("We received following pattern from RSyslog {0}").format(pattern)
# os.system('logger -t montag -p user.info ' + info)

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company, room_id = get_credentials()

last = ""
with open("/var/log/devices/lastlog_ddos.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_ddos.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_ddos.json", "r", errors='ignore') as log_file:
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
        print("File /var/log/devices/lastlog_ddos.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_ddos.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_ddos.json - Index error in regex")
        exit()

    try:
        ddos_type = re.findall(r"Denial of Service attack detected: <(.*?)>", msg)[0]
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_power_supply_down.json - Index error in regex")
        exit()

set_portnumber("0")
set_decision(ipadd, "4")
if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
    print("Less than 5 min")
    syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
    exit(0)

notif = ("A Denial Of Service Attack is detected on OmniSwitch ({0}/{1}) of type {2}").format(host,ipadd,ddos_type)
syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API")
send_message(notif)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
set_decision(ipadd, "4")
try:
    mysql_save(runtime=runtime, ip_address=ipadd, result='success', reason=notif, exception='')
    syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision")    
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass   

# Enable debugging logs for getting IP Attacker's IP Address "swlog appid ipv4 subapp all level debug3"
appid = "ipv4"
subapp = "all"
level = "debug3"
# Call debugging function from support_tools_OmniSwitch
syslog.syslog(syslog.LOG_INFO, "Call debugging function from support_tools_OmniSwitch - swlog appid ipv4 subapp all level debug3")
debugging(switch_user, switch_password, ipadd, appid, subapp, level)
syslog.syslog(syslog.LOG_INFO, "Debugging applied")

# clear lastlog file
open('/var/log/devices/lastlog_ddos.json', 'w').close()