#!/usr/bin/env python

import sys
import os
import json
from support_tools_OmniSwitch import get_credentials, debugging
from time import strftime, localtime
# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
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
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog.json empty")
        exit()

# Enable debugging logs for getting IP Attacker's IP Address "swlog appid bcmd subapp 3 level debug2"
appid = "bcmd"
subapp = "3"
level = "debug2"
# Call debugging function from support_tools_OmniSwitch
print("call function enable debugging")
debugging(switch_user, switch_password, ipadd, appid, subapp, level)
os.system('logger -t montag -p user.info Process terminated')

# clear lastlog file
open('/var/log/devices/lastlog.json', 'w').close()

sys.exit(0)
