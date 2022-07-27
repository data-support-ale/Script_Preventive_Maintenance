#!/usr/bin/env python3

import sys
import os
import re
import json
import syslog
from support_tools_OmniSwitch import get_credentials
from time import strftime, localtime, sleep
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

# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company, room_id = get_credentials()

# Log sample
# OS6860E_VC_Core swlogd ospf_nbr.c ospfNbrStateMachine 0 ospf_0 STATE EVENT: CUSTLOG CMM OSPF neighbor state change for 172.25.136.2, router-id 172.25.136.2: FULL to DOWN

last = ""
with open("/var/log/devices/lastlog_ospf.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_ospf.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_ospf.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]

    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_ospf.json empty")
        exit()

    neighbor_ipadd, router_id, initial_state, final_state = re.findall(
        r"CUSTLOG CMM OSPF neighbor state change for (.*?), router-id (.*?): (.*?) to (.*)", msg)[0]

set_portnumber("0")
if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
    print("Less than 5 min")
    exit(0)


if "FULL" in final_state:
    notif = ("Preventive Maintenance Application - OSPF Neighbor state change on OmniSwitch {0} / {1}.\n\nDetails:\n- Router-ID: {2}\n- Neighbor-ID {3}\n- Initial State: {4}\n- Final State: {5}.").format(host,ipadd,router_id,neighbor_ipadd,initial_state,final_state)
else:
    notif = ("Preventive Maintenance Application - OSPF Neighbor state change on OmniSwitch {0} / {1}.\n\nDetails:\n- Router-ID: {2}\n- Neighbor-ID {3}\n- Initial State: {4}\n- Final State: {5}\nPlease check the OSPF Neighbor node connectivity.").format(host,ipadd,router_id,neighbor_ipadd,initial_state,final_state)

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

