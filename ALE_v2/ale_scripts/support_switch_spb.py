#!/usr/bin/env python3

import sys
import os
import re
import json
from support_tools_OmniSwitch import get_credentials, collect_command_output_spb
from time import strftime, localtime, sleep
from support_send_notification import *
# from database_conf import *
import time
import syslog

syslog.openlog('support_switch_spb')
syslog.syslog(syslog.LOG_INFO, "Executing script")

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
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company, room_id = get_credentials()

# Log sample
#{"@timestamp":"2022-01-11T14:30:23+01:00","type":"syslog_json","relayip":"10.130.7.245","hostname":"os6900_vc_core","message":"<134>Jan 11 14:30:23 OS6900_VC_Core swlogd isis_spb_0 ADJACENCY INFO: Lost L1 adjacency with e8e7.32f5.b58b on ifId 1013","end_msg":""}

last = ""
with open("/var/log/devices/lastlog_spb.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_spb.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_spb.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ip = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_spb.json empty")
        exit()

    adjacency_id, port_1 = re.findall(r"Lost L1 adjacency with (.*?) on ifId (.*)", msg)[0]
    n = len(str(port_1))
    print(n)
    dig = []
    dig = list(int(port_1) for port_1 in str(port_1))
    if n < 6:
        dig_1 = [1, 0]
        dig = dig_1 + dig
    unit = dig[0]
    slot = dig[2]
    port = str(dig[4]) + str(dig[5])

    port = str(unit) + "/" + str(slot) + "/" + str(port)
    port = "Port " + port
    if n > 6:
        if str(dig[6]) != "0":
            port = str(dig[6]) + str(dig[7])
            port = "Linkagg " + port
        else:
            port = str(dig[7])
            port = "Linkagg " + port
    print(port)

set_portnumber(port)
if alelog.rsyslog_script_timeout(ip + port + pattern, time.time()):
    print("Less than 5 min")
    exit(0)

if jid1 != '' or jid2 != '' or jid3 != '':
    filename_path, subject, action, result, category = collect_command_output_spb(switch_user, switch_password, host, ip, adjacency_id, port)
    syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
    syslog.syslog(syslog.LOG_INFO, "Action: " + action)
    syslog.syslog(syslog.LOG_INFO, "Result: " + result)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")  
    set_decision(ip, "4")
    mysql_save(runtime=_runtime, ip_address=ip, result='success', reason=action, exception='')
    # send_message(notif, jid)
    send_file_detailed(filename_path, subject, action, result, category)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
else:
    set_decision(ip, "4")
    mysql_save(runtime=_runtime, ip_address=ip, result='success', reason="Mail request set as no", exception='')

    print("Mail request set as no")
    os.system('logger -t montag -p user.info Mail request set as no')
    sleep(1)
    open('/var/log/devices/lastlog_spb.json', 'w').close()
