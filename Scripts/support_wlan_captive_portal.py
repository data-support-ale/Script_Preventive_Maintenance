#!/usr/local/bin/python3.7

import sys
import os
import re
import json
from support_tools_OmniSwitch import get_credentials
from time import strftime, localtime, sleep
from support_send_notification import send_message
from database_conf import *

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

# Log sample
#{"@timestamp":"2022-01-11T14:30:23+01:00","type":"syslog_json","relayip":"10.130.7.245","hostname":"os6900_vc_core","message":"<134>Jan 11 14:30:23 OS6900_VC_Core swlogd isis_spb_0 ADJACENCY INFO: Lost L1 adjacency with e8e7.32f5.b58b on ifId 1013","end_msg":""}

last = ""
nbr = 0
with open("/var/log/devices/lastlog_captiveportal.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_captiveportal.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_captiveportal.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ip = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_captiveportal.json empty")
        exit()
    except IndexError:
        print("Index error in regex")
        exit()
    f = msg.split(',')
    for element in f:
        if "portal" in element:
            try:
               status = re.findall(r"portal/(.*)", msg)[0]
               print(status)
            except IndexError:
                print("Index error in regex")
                exit()
        elif "open" in element:
            try:
               status = re.findall(r"open/(.*)", msg)[0]
               print(status)
            except IndexError:
                print("Index error in regex")
                exit()

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"status": status}, "fields": {"count": 1}}])
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass 