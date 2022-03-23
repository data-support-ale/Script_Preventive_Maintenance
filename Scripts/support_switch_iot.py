#!/usr/local/bin/python3.7

from distutils.log import info
import sys
import os
import json
from time import strftime, localtime
from support_tools_Stellar import get_credentials, send_file, ssh_connectivity_check
from support_send_notification import send_message
from database_conf import *
import re

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

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

    # Sample log
    # Stellar AP log: iot_ins.c|1182: iot_sta_info_report mqtt disconnect or is empty
    if "mqtt disconnect or is empty" in msg:
        try:
            cmd = "cat /tmp/config/iot.conf"
            output = ssh_connectivity_check(login_AP, pass_AP, ipadd, cmd)
            if "Disable" in output:
                print("IoT Profiling disabled")
                service_status = "Disabled"
            else:
                service_status = "Enabled"

            info = ("IoT Profiling module disconnected on the Stellar AP {0} - IoT Service is {1}").format(ipadd, service_status)
            send_message(info,jid)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "MQTT Status": "mqtt disconnect or is empty"}, "fields": {"count": 1}}])
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
            send_message(info,jid)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "MQTT Status": "Unable to connect"}, "fields": {"count": 1}}])
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
