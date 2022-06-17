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

print(sys.executable)
# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
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
        ip = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_authfail.json empty")
        exit()
    except IndexError:
        print("Index error in regex")
        exit()
    try:
        user, source_ip, protocol = re.findall(r"Login by (.*?) from (.*?) through (.*?) Failed", msg)[0]
    except IndexError:
        print("Index error in regex")
        exit()

info = "Preventive Maintenance Application - Authentication failed on OmniSwitch {0} / {1}\n\nDetails:\n- User Login : {2}\n- Source IP Address : {3}\n- Protocol : {4}\n".format(host, ip, user, source_ip, protocol)
send_message(info, jid)

sleep(1)
open('/var/log/devices/lastlog_authfail.json', 'w').close()

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                    "user": user, "IP": ip, "protocol": protocol, "source_ip": source_ip}, "fields": {"count": 1}}])
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass
