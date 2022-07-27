#!/usr/bin/env python3

import sys
import os
import getopt
import json
import logging
import datetime
from time import strftime, localtime
from support_tools_OmniSwitch import get_credentials, collect_command_output_ps
from support_send_notification import *
import subprocess
# from database_conf import *
import re
import time

from pattern import set_rule_pattern, set_portnumber, set_decision, mysql_save

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)

pattern = sys.argv[1]
print(pattern)
set_rule_pattern(pattern)
# info = ("We received following pattern from RSyslog {0}").format(pattern)
# os.system('logger -t montag -p user.info ' + info)

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company, room_id = get_credentials()

last = ""
with open("/var/log/devices/lastlog_power_supply_down.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_power_supply_down.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_power_supply_down.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_power_supply_down.json empty")
        exit()
        
    set_portnumber("0")
    set_decision(ipadd, "4")
    if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
        print("Less than 5 min")
        exit(0)

    # Sample log
    # OS6860E swlogd ChassisSupervisor Power Mgr INFO: Power Supply 1 Removed
    if "Removed" in msg:
        try:
            nb_power_supply = re.findall(r"Power Supply (.*?) Removed", msg)[0]
            filename_path, subject, action, result, category = collect_command_output_ps(switch_user, switch_password, nb_power_supply, host, ipadd)
            send_file_detailed(subject, jid1, action, result, company, filename_path)
            print(action)
            try:
                mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')
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
    # OS6860E swlogd ChassisSupervisor MipMgr EVENT: CUSTLOG CMM chassisTrapsAlert - Power supply is inoperable: PS 2
    elif "inoperable" in msg:
        try:
            nb_power_supply = re.findall(r"Power supply is inoperable: PS (.*)", msg)[0]
            info = "A default on Power supply {} from device {} has been detected".format(nb_power_supply, ipadd)
            print(info)
            send_message_detailed(info, jid1, jid2, jid3)
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
    # OS6860E swlogd ChassisSupervisor MipMgr EVENT: CUSTLOG CMM Device Power Supply operational state changed to UNPOWERED
    elif "UNPOWERED" in msg:
        try:
            info = "A default on Power supply \"Power Supply operational state changed to UNPOWERED\" from device {} has been detected".format(ipadd)
            print(info)
            send_message_detailed(info, jid1, jid2, jid3)
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
