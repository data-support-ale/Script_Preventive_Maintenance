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
with open("/var/log/devices/lastlog_vc_down.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_vc_down.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_vc_down.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_vc_down.json empty")
        exit()
        
    set_portnumber("0")
    set_decision(ipadd, "4")
    if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
        print("Less than 5 min")
        exit(0)
	
    # Sample log
    # swlogd: ChassisSupervisor bootMgr info(5) bootMgrVCMTopoDataEventHandler: remote chassis 3 no longer in the topology - closing
    if "bootMgrVCMTopoDataEventHandler" in msg:
        try:
            nb_vc = re.findall(
                r"bootMgrVCMTopoDataEventHandler: remote chassis (.*?) no longer in the topology", msg)[0]
            info = "The Virtual Chassis Unit " + nb_vc + \
                " of OmniSwitch \"" + host + "\" IP: " + ipadd + " is DOWN"
            # send_message_detailed(info, jid1, jid2, jid3)
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
    # swlogd intfCmm Mgr INFO: cmmEsmHandleNIDown: Rxed CSLIB_EVENT_NIDOWN event for chassis=2 slot=1, module=101065220
    elif "cmmEsmHandleNIDown" in msg:
        try:
            nb_vc = re.findall(
                r"CSLIB_EVENT_NIDOWN event for chassis=(.*?) slot", msg)[0]
            info = "The Virtual Chassis Unit " + nb_vc + \
                " of OmniSwitch \"" + host + "\" IP: " + ipadd + " is DOWN"
            # send_message_detailed(info, jid1, jid2, jid3)
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
    # swlogd ChassisSupervisor bootMgr EVENT: CUSTLOG CMM Sending VC Takeover to NIs and applications
    elif "VC Takeover" in msg:
        info = "The Virtual Chassis \"" + host + \
            "\" IP: " + ipadd + " is doing a TakeOver"
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3)
        try:
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=info, exception='')
        except UnboundLocalError as error:
            print(error)
            sys.exit()
    # Sample log
    # swlogd ChassisSupervisor MipMgr EVENT: CUSTLOG CMM The switch was restarted by the user
    # swlogd ChassisSupervisor MipMgr EVENT: CUSTLOG CMM The switch was restarted by a power cycle or due to some type of failure
    elif "The switch was restarted by" in msg:
        try:
            reason = re.findall(r"The switch was restarted by (.*)", msg)[0]
            info = "The Virtual Chassis \"" + host + \
                "\" IP: " + ipadd + " did reload by " + reason
            print(info)
            # send_message_detailed(info, jid1, jid2, jid3)
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
