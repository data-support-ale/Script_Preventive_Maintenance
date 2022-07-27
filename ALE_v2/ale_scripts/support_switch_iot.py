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
import support_tools_Stellar
import time

from pattern import set_rule_pattern, set_portnumber, set_decision, mysql_save

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

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

# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company, room_id = get_credentials()

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
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_iot.json empty")
        exit()
    except IndexError:
        print("Index error in regex")
        exit()

    set_portnumber("0")
    set_decision(ipadd, "4")
    if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
        print("Less than 5 min")
        exit(0)

    # Sample log
    # Stellar AP log: iot_ins.c|1182: iot_sta_info_report mqtt disconnect or is empty
    if "mqtt disconnect or is empty" in msg:
        try:
            ipadd="10.130.7.184"
            cmd = "cat /tmp/config/iot.conf"
            output = ssh_connectivity_check(login_AP, pass_AP, ipadd, cmd)
            if output != None:
                output = str(output)
                output = bytes(output, "utf-8").decode("unicode_escape")
                output = output.replace("', '","")
                output = output.replace("']","")
                output = output.replace("['","")
                print(output)
            if "Disable" in output:
                print("IoT Profiling disabled")
                service_status = "Disabled"
            else:
                service_status = "Enabled"

            info = ("IoT Profiling module disconnected on the Stellar AP {0} - IoT Service is {1} on AP").format(ipadd, service_status)
            # send_message(info,jid)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=info, exception='')
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
            ov_ip = re.findall(r"Unable to connect (.*?):1883", msg)[0]
            info = ("IoT Profiling module is enabled but OmniSwitch {0} / {1} cannot reach OmniVista IP Address {2} port 1883 - please ensure OmniVista is reachable from default-VRF (Device Profiling feature is not VRF-Aware)").format(ipadd, host, ov_ip)
            # send_message(info,jid)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=info, exception='')
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
        sys.exit()
