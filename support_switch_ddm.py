#!/usr/local/bin/python3.7

import sys
import os
import re
import json
import subprocess
import datetime
from time import strftime, localtime, sleep
from support_tools_OmniSwitch import get_credentials, ssh_connectivity_check
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

    try:
        sfp_power, slot, port, threshold = re.findall(r"Power=(.*?) dBm on slot=(.*?) port=(.*?), crossed DDM threshold (.*)", msg)[0]
    except IndexError:
        print("Index error in regex")
        exit()

if jid != '':
    notif = "The SFP " + slot + "/" + port + " on OmniSwitch \"" + host + "\" IP: " + \
        ipadd + " crossed DDM threshold " + threshold + " Power: " + sfp_power + " dBm"
    send_message(notif, jid)
else:
    print("Mail request set as no")
    os.system('logger -t montag -p user.info Mail request set as no')
    sleep(1)
    open('/var/log/devices/lastlog_ddm.json', 'w', errors='ignore').close()

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                    "IP": ipadd, "Port": slot + '/' + port, "Threshold": threshold, "Power": sfp_power}, "fields": {"count": 1}}])
except UnboundLocalError as error:
    print(error)
    sys.exit()

##########################Get More LOGS########################################
text = "########################################################################"
text = "More logs related to the Digital Diagnostics Monitoring (DDM) noticed on OmniSwitch: {0} \n\n\n".format(
    ipadd)
text = "########################################################################"

l_switch_cmd = []
l_switch_cmd.append("show interfaces")
l_switch_cmd.append("show interfaces status")
l_switch_cmd.append("show system")
l_switch_cmd.append("show transceivers slot " + slot + "/1")
l_switch_cmd.append("show lldp remote-system")

print(ipadd)
for switch_cmd in l_switch_cmd:
    cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
        switch_password, switch_user, ipadd, switch_cmd)
    try:
        output = ssh_connectivity_check(
            switch_user, switch_password, ipadd, switch_cmd)
        output = subprocess.check_output(
            cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
        if output != None:
            output = output.decode('UTF-8').strip()
            text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output)
        else:
            exception = "Timeout"
            info = (
                "Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                    "Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            sys.exit()
    except subprocess.TimeoutExpired as exception:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                "Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        sys.exit()
    except FileNotFoundError as exception:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                "Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        sys.exit()

date = datetime.date.today()
date_hm = datetime.datetime.today()

filename = "{0}_{1}-{2}_{3}_logs".format(date,
                                         date_hm.hour, date_hm.minute, ipadd)
f_logs = open(
    '/opt/ALE_Script/{0}_ddm.txt'.format(filename), 'w', errors='ignore')
f_logs.write(text)
f_logs.close()
###############################################################################

#### Send file with additionnal logs #####
filename = '/opt/ALE_Script/{0}.txt'.format(filename)
print(filename)

if jid != '':
    #         send_file(info,jid,ipadd,filename)
    print("file attached in Rainbow bubble")
