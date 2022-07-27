#!/usr/bin/env python3

import sys
import os
from time import strftime, localtime
import re
from support_tools_OmniSwitch import get_credentials
from support_send_notification import *
import json
import time

from pattern import set_rule_pattern, set_portnumber, set_decision, mysql_save

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

script_name = sys.argv[0]
pattern = sys.argv[1]
print(pattern)
set_rule_pattern(pattern)
os.system('logger -t montag -p user.info Executing script ' + script_name + ' pattern: ' + pattern)

switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company, room_id = get_credentials()

last = ""
with open("/var/log/devices/lastlog_wlan_operations.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_wlan_operations.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_wlan_operations.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_wlan_operations.json empty")
        exit()
    # Sysreboot operation on Stellar AP
    if "sysreboot" in msg:
        try:

            set_portnumber("0")
            set_decision(ipadd, "4")
            if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
                print("Less than 5 min")
                exit(0)

            os.system('logger -t montag -p user.info reboot detected')
            subject = ("Preventive Maintenance Application - There is an unexpected reboot detected on server {0} from WLAN Stellar AP {1}").format(ip_server, ipadd)
            action = "Please check the LANPOWER is running fine on LAN OmniSwitch and verify the capacitor-detection is disabled"
            result = "More details in the Technical Knowledge Base https://myportal.al-enterprise.com/alebp/s/tkc-redirect?000066402"
            send_message_detailed(subject, jid1, jid2, jid3)
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()

        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=subject, exception='')
        sys.exit(0)
    # Sysupgrade operation on Stellar AP
    elif "sysupgrade" in msg:
        try:

            set_portnumber("0")
            set_decision(ipadd, "4")
            if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
                print("Less than 5 min")
                exit(0)


            upgrade_version = re.findall(r"-v(.*)ww", msg)[0]
            os.system('logger -t montag -p user.info internal error detected')
            subject = ("Preventive Maintenance Application - There is an upgrade detected on server {0} from WLAN Stellar AP: {1} - Version: {2}").format(ip_server, ipadd, upgrade_version)
            action = " "
            result = " "
            send_message_detailed(subject, jid1, jid2, jid3)
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()

        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=subject, exception='')
        sys.exit(0)

    else:
        print("Script support_wlan_operations no pattern match - exiting script")
        sys.exit()
