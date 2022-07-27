#!/usr/bin/env python3

import sys
import os
import json
from support_tools_OmniSwitch import get_credentials, debugging
from time import strftime, localtime
import time
import syslog

syslog.openlog('support_switch_debugging_network_loop')
syslog.syslog(syslog.LOG_INFO, "Executing script")


from pattern import set_rule_pattern, set_portnumber, set_decision

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

# Script init
script_name = sys.argv[0]

pattern = sys.argv[1]
# pattern = 'Buffer list is empty'
print(pattern)
set_rule_pattern(pattern)
# info = ("We received following pattern from RSyslog {0}").format(pattern)
# os.system('logger -t montag -p user.info ' + info)

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

print(sys.executable)

# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company, room_id = get_credentials()

last = ""
with open("/var/log/devices/lastlog.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog.json", "r", errors='ignore') as log_file:
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
        print("File /var/log/devices/lastlog.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog.json - JSONDecodeError")
        exit()


set_portnumber("0")
set_decision(ipadd, "4")
if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
    print("Less than 5 min")
    exit(0)

# Enable debugging logs for getting IP Attacker's IP Address "swlog appid bcmd subapp 3 level debug2"
appid = "slNi"
subapp = "20"
level = "debug2"
# Call debugging function from support_tools_OmniSwitch
print("call function enable debugging - swlog appid slNi subapp 20 level debug2")
syslog.syslog(syslog.LOG_INFO, "Call debugging function from support_tools_OmniSwitch - swlog appid slNI subapp 20 level debug2")
debugging(switch_user, switch_password, ipadd, appid, subapp, level)
syslog.syslog(syslog.LOG_INFO, "Debugging applied")

# clear lastlog file
open('/var/log/devices/lastlog.json', 'w').close()
