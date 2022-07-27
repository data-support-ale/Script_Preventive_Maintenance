#!/usr/local/bin/python3.7

import sys
import os
import re
import json
from time import strftime, localtime, sleep
from support_tools_OmniSwitch import get_credentials, collect_command_output_ddm
from support_send_notification import *
from time import strftime, localtime, sleep
from database_conf import *
import syslog

syslog.openlog('support_switch_ddm')
syslog.syslog(syslog.LOG_INFO, "Executing script")

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]
chassis = "1"
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

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


filename_path, subject, action, result, category = collect_command_output_ddm(switch_user, switch_password, host, ipadd, chassis, port, slot, ddm_type, threshold, sfp_power)
syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
syslog.syslog(syslog.LOG_INFO, "Action: " + action)
syslog.syslog(syslog.LOG_INFO, "Result: " + result)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API")
send_file_detailed(filename_path, subject, action, result, category)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Port": slot + '/' + port, "Threshold": threshold, ddm_type: sfp_power}, "fields": {"count": 1}}])
    syslog.syslog(syslog.LOG_INFO, "Statistics saved")
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass