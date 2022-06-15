#!/usr/local/bin/python3.7

import sys
import os
import re
import json
from time import strftime, localtime, sleep
from support_tools_OmniSwitch import get_credentials, ssh_connectivity_check, collect_command_output_ddm, send_file
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
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_ddm.json empty")
        exit()
    except IndexError:
        print("Index error in regex")
        exit()
   # Log sample: cmmEsmCheckDDMThresholdViolations: SFP/XFP Supply Current=8.6 mA on slot=1 port=34, crossed DDM threshold high warning
    try:
        ddm_type, sfp_power, slot, port, threshold = re.findall(r"SFP/XFP (.*?)=(.*?) on slot=(.*?) port=(.*?), crossed DDM threshold (.*)", msg)[0]
        # Log sample cmmEsmCheckDDMThresholdViolations: SFP/XFP Tx Optical Power=-inf dBm on slot=1 port=28, crossed DDM threshold low alarm
        if sfp_power == "-inf dBm":
            print("DDM event generated when interface is administratively DOWN")
            os.system('logger -t montag -p user.info Executing script support_switch_ddm - DDM event generated when interface is administratively DOWN - exit')
            exit()
    except IndexError:
        print("Index error in regex")
        os.system('logger -t montag -p user.info Executing script support_switch_ddm - Index error in regex - exit')
        exit()

filename_path, subject, action, result, category = collect_command_output_ddm(switch_user, switch_password, host, ipadd, port, slot, ddm_type, threshold, sfp_power)
send_file(filename_path, subject, action, result, category, jid)


try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Port": slot + '/' + port, "Threshold": threshold, ddm_type: sfp_power}, "fields": {"count": 1}}])
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass

