#!/usr/local/bin/python3.7

import sys
import os
import json
from support_tools_OmniSwitch import get_credentials, debugging
from time import strftime, localtime
import syslog

syslog.openlog('support_switch_debugging_network_loop')
syslog.syslog(syslog.LOG_INFO, "Executing script")


runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

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
        syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + msg)
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog.json - JSONDecodeError")
        exit()

# Enable debugging logs for getting IP Attacker's IP Address "swlog appid slNI subapp 20 level debug2"
# Swlog format: slNi MACMOVE DBG2: macCallBackProcessing_t[1174] [u:0][INS]: c/s/p: 1/1/14  d:vlan(1) MAC: 00:80:9f:57:df:33 vid:68 p:13 b:bridging t:learned e:0 dup:0 L3:0 cpu:0 mbi:0 McEntryNew:
appid = "slNi"
subapp = "20"
level = "debug2"
# Call debugging function from support_tools_OmniSwitch
print("call function enable debugging")
syslog.syslog(syslog.LOG_INFO, "Call debugging function from support_tools_OmniSwitch - swlog appid slNI subapp 20 level debug2")
debugging(switch_user, switch_password, ipadd, appid, subapp, level)
syslog.syslog(syslog.LOG_INFO, "Debugging applied")

# clear lastlog file
open('/var/log/devices/lastlog.json', 'w').close()

sys.exit(0)
