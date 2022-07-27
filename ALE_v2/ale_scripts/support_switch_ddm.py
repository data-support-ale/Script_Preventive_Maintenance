#!/usr/bin/env python3

import sys
import os
import re
import json
import syslog
from time import strftime, localtime
from support_tools_OmniSwitch import get_credentials, collect_command_output_ddm
from time import strftime, localtime
from support_send_notification import *
# from database_conf import *
import time
import syslog

syslog.openlog('support_switch_ddm')
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

path = os.path.dirname(__file__)

# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company, room_id = get_credentials()

# Log sample
# OS6860E_VC_Core swlogd intfCmm Mgr WARN: cmmEsmCheckDDMThresholdViolations: SFP/XFP Rx Power=-26.8 dBm on slot=1 port=9, crossed DDM threshold low alarm

last = ""
with open("/var/log/devices/lastlog_ddm.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_ddm.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_ddm.json", "r", errors='ignore') as log_file:
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
        print("File /var/log/devices/lastlog_ddm.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_ddm.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_ddm.json - Index error in regex")
        exit()
   # Log sample: cmmEsmCheckDDMThresholdViolations: SFP/XFP Supply Current=8.6 mA on slot=1 port=34, crossed DDM threshold high warning
    try:
        ddm_type, sfp_power, slot, port, threshold = re.findall(r"SFP/XFP (.*?)=(.*?) on slot=(.*?) port=(.*?), crossed DDM threshold (.*)", msg)[0]
        # Log sample cmmEsmCheckDDMThresholdViolations: SFP/XFP Tx Optical Power=-inf dBm on slot=1 port=28, crossed DDM threshold low alarm
    except IndexError:
        try:
            ddm_type, sfp_power, chassis, slot, port, threshold = re.findall(r"SFP/XFP (.*?)=(.*?) on chassis=(.*?) slot=(.*?) port=(.*?), crossed DDM threshold (.*)", msg)[0]
            # Log sample AOS 8.9R01 OS6900_VC swlogd intfCmm Mgr WARN: cmmEsmCheckDDMThresholdViolations: SFP/XFP Rx Power=-26.6 dBm on chassis=2 slot=1 port=9, crossed DDM threshold low alarm

        except IndexError:
                print("Index error in regex")
                syslog.syslog(syslog.LOG_INFO, "Index error in regex")
                exit()
    if sfp_power == "-inf dBm":
            print("DDM event generated when interface is administratively DOWN")
            syslog.syslog(syslog.LOG_INFO, "DDM event generated when interface is administratively DOWN - exit")
            exit()

set_portnumber(port)
if alelog.rsyslog_script_timeout(ipadd + port + pattern, time.time()):
    print("Less than 5 min")
    syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
    exit(0)

syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_ddm")
filename_path, subject, action, result, category = collect_command_output_ddm(switch_user, switch_password, host, ipadd, port, slot, ddm_type, threshold, sfp_power)
print(subject)
syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
syslog.syslog(syslog.LOG_INFO, "Action: " + action)
syslog.syslog(syslog.LOG_INFO, "Result: " + result)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API")
send_file(filename_path, subject, action, result, category)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
set_decision(ipadd, "4")
try:
    mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')
    syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision")    
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass
