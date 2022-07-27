#!/usr/bin/env python3

import sys
import os
import json
import re
from time import strftime, localtime
from support_tools_OmniSwitch import get_credentials
from support_send_notification import *
# from database_conf import *
import time

from pattern import set_rule_pattern, set_portnumber, set_decision, mysql_save

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

pattern = sys.argv[1]
print(pattern)
set_rule_pattern(pattern)
# info = ("We received following pattern from RSyslog {0}").format(pattern)
# os.system('logger -t montag -p user.info ' + info)

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company, room_id = get_credentials()

last = ""
with open("/var/log/devices/lastlog_radius_down.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_radius_down.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_radius_down.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_radius_down.json empty")
        exit()

    set_portnumber("0")
    set_decision(ipadd, "4")
    if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
        print("Less than 5 min")
        exit(0)

    # Sample log
    # swlogd radCli main INFO: RADIUS Primary Server - UPAM_Radius_Server is DOWN
    if "RADIUS Primary Server" in msg:
        try:
            radius_server, status = re.findall(r"RADIUS Primary Server - (.*?) is (.*)", msg)[0]
            info = "The Primary Radius Server " + radius_server + " set on the OmniSwitch " + host + "\" IP: " + ipadd + " aaa settings is " + status
            
            send_message(info)
            try:
                mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=info, exception='')
            except UnboundLocalError as error:
                print(error)
                sys.exit()
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
    # Sample log
    # swlogd radCli main INFO: RADIUS Backup Server - UPAM_Radius_Server is DOWN
    elif "RADIUS Backup Server" in msg:
        try:
            radius_server, status = re.findall(r"RADIUS Backup Server - (.*?) is (.*)", msg)[0]
            info = "The Primary Radius Server " + radius_server + " set on the OmniSwitch " + host + "\" IP: " + ipadd + " aaa settings is " + status
            
            send_message(info)
            try:
                mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=info, exception='')
            except UnboundLocalError as error:
                print(error)
                sys.exit()
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
    else:
        print("no pattern match - exiting script")
        sys.exit()