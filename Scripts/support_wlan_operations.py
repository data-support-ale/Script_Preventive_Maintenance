#!/usr/bin/env python3

import sys
import os
from time import strftime, localtime
import re
from support_tools_OmniSwitch import get_credentials
from support_send_notification import *
import json
import time

#### To Add in rsyslog.conf ####
#template (name="wlanlogoperations" type="string"
#     string="/var/log/devices/lastlog_wlan_operations.json")

#if $msg contains 'sysreboot' then {
#     $RepeatedMsgReduction on
#     if $msg contains 'Power Off' then {
#          action(type="omfile" DynaFile="wlanlogoperations" template="json_syslog" DirCreateMode="0755" FileCreateMode="0755")
#          action(type="omprog"  binary="/opt/preventive-maintenance-2.1.8/ALE_v2/ale_scripts/support_wlan_operations.py \"sysreboot;and;Power Off\"")
#          stop
#     }
#}

#if $msg contains 'osupgrade' and $msg contains 'sysupgrade' then {
#     $RepeatedMsgReduction on
#     action(type="omfile" DynaFile="wlanlogoperations" template="json_syslog" DirCreateMode="0755" FileCreateMode="0755")
#     action(type="omprog" name="support_wlan_generic_upgrade" binary="/opt/preventive-maintenance-2.1.8/ALE_v2/ale_scripts/support_wlan_operations.py \"osupgrade;and;sysupgrade\"")
#     stop
#}


path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))

_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

script_name = sys.argv[0]

os.system('logger -t montag -p user.info Executing script ' + script_name )

switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

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
            os.system('logger -t montag -p user.info reboot detected')
            subject = ("Preventive Maintenance Application - There is an unexpected reboot detected on server {0} from WLAN Stellar AP {1}").format(ip_server, ipadd)
            action = "Please check the LANPOWER is running fine on LAN OmniSwitch and verify the capacitor-detection is disabled"
            result = "More details in the Technical Knowledge Base https://myportal.al-enterprise.com/alebp/s/tkc-redirect?000066402"
            filename_path = "/var/log/devices/lastlog_wlan_operations.json"
            category = "sysreboot"
            send_file(filename_path, subject, action, result, category, jid)
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
        sys.exit(0)
    # Sysupgrade operation on Stellar AP
    elif "sysupgrade" in msg:
        try:
            upgrade_version = re.findall(r"-v(.*)ww", msg)[0]
            os.system('logger -t montag -p user.info internal error detected')
            subject = ("Preventive Maintenance Application - There is an upgrade detected on server {0} from WLAN Stellar AP: {1} - Version: {2}").format(ip_server, ipadd, upgrade_version)
            action = " "
            result = " "
            filename_path = "/var/log/devices/lastlog_wlan_operations.json"
            category = "sysreboot"
            send_file(filename_path, subject, action, result, category, jid)
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
        sys.exit(0)

    else:
        print("Script support_wlan_operations no pattern match - exiting script")
        sys.exit()