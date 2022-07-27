#!/usr/bin/env python3

from distutils.log import info
import sys
import os
import json
from time import strftime, localtime
from support_tools_Stellar import get_credentials,  ssh_connectivity_check
from support_send_notification import *
# from database_conf import *
import re
import time
import syslog

syslog.openlog('support_switch_iot')
syslog.syslog(syslog.LOG_INFO, "Executing script")


from pattern import set_rule_pattern, set_portnumber, set_decision, mysql_save

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

# Script init
script_name = sys.argv[0]

pattern = sys.argv[1]
print(pattern)
set_rule_pattern(pattern)
# info = ("We received following pattern from RSyslog {0}").format(pattern)
# os.system('logger -t montag -p user.info ' + info)

# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company, room_id = get_credentials()

last = ""
with open("/var/log/devices/lastlog_iot.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_iot.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_iot.json", "r", errors='ignore') as log_file:
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
        print("File /var/log/devices/lastlog_iot.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_iot.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_iot.json - Index error in regex")
        exit()

set_portnumber("0")
set_decision(ipadd, "4")
if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
    print("Less than 5 min")
    syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
    exit(0)

# Sample log
# Stellar AP log: iot_ins.c|1182: iot_sta_info_report mqtt disconnect or is empty
if "mqtt disconnect or is empty" in msg:
    try:
        pattern = "mqtt disconnect or is empty"
        syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
        cmd = "cat /tmp/config/iot.conf"
        syslog.syslog(syslog.LOG_INFO, "SSH Session started on OmniSwitch " + ipadd)
        output = ssh_connectivity_check(login_AP, pass_AP, ipadd, cmd)
        if output != None:
            output = str(output)
            output = bytes(output, "utf-8").decode("unicode_escape")
            output = output.replace("', '","")
            output = output.replace("']","")
            output = output.replace("['","")
            print(output)
        if output == None:
            service_status = "Disabled"
            pass
        elif "Disable" in output:
            print("IoT Profiling disabled")
            service_status = "Disabled"
        else:
            service_status = "Enabled"
        syslog.syslog(syslog.LOG_INFO, "Service Status: " + service_status)
        notif = ("Preventive Maintenance Application - IoT Profiling module disconnected on the WLAN Stellar AP {0} - IoT Service is {1}.").format(ipadd, service_status)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
        send_message(notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

        try:
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass 
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except IndexError as error:
        print(error)
        sys.exit()
# Sample log
# OS6860E swlogd mqttd main ERR: mqttdClientConnect@620: Unable to connect 143.209.0.2:1883 (Connection timed out)
elif "Unable to connect" in msg:
    try:
        pattern = "mqtt disconnect or is empty"
        syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
        ov_ip = re.findall(r"Unable to connect (.*?):1883", msg)[0]
        notif = ("Preventive Maintenance Application - IoT Profiling module is enabled but OmniSwitch {0} / {1} cannot reach OmniVista IP Address {2} port 1883 - please ensure OmniVista is reachable from default-VRF (Device Profiling feature is not VRF-Aware)").format(ipadd, host, ov_ip)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
        send_message(notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass 
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except IndexError as error:
        print(error)
        sys.exit()
else:
    print("no pattern match - exiting script")
    syslog.syslog(syslog.LOG_INFO, "No pattern match - exiting script")
    sys.exit()
