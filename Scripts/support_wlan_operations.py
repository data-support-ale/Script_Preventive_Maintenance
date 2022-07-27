#!/usr/bin/env python3

import sys
import os
from time import strftime, localtime
import re
from support_tools_OmniSwitch import get_credentials
from support_send_notification import *
import json
import time
import syslog

syslog.openlog('support_wlan_operations')
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
        print(msg)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog IP Address: " + ipadd)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog Host: " + host)
        #syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + msg)
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_wlan_operations.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_wlan_operations.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_wlan_operations.json - Index error in regex")
        exit()
    # Sysreboot operation on Stellar AP
    if "sysreboot" in msg:
        try:
            pattern = "sysreboot"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            subject = ("Preventive Maintenance Application - There is an unexpected reboot detected on server {0} from WLAN Stellar AP {1}").format(ip_server, ipadd)
            action = "Please check the LANPOWER is running fine on LAN OmniSwitch and verify the capacitor-detection is disabled"
            result = "More details in the Technical Knowledge Base https://myportal.al-enterprise.com/alebp/s/tkc-redirect?000066402"
            filename_path = "/var/log/devices/lastlog_wlan_operations.json"
            category = "sysreboot"
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")            
            send_file_detailed(filename_path, subject, action, result, category)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
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
            pattern = "sysupgrade"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)            
            upgrade_version = re.findall(r"-v(.*)ww", msg)[0]
            syslog.syslog(syslog.LOG_INFO, "Upgrade version: " + upgrade_version) 
            subject = ("Preventive Maintenance Application - There is an upgrade detected on server {0} from WLAN Stellar AP: {1} - Version: {2}").format(ip_server, ipadd, upgrade_version)
            action = " "
            result = " "
            filename_path = "/var/log/devices/lastlog_wlan_operations.json"
            category = "sysreboot"
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")            
            send_file_detailed(filename_path, subject, action, result, category)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
        sys.exit(0)

    else:
        print("Script support_wlan_exceptions no pattern match - exiting script")
        syslog.syslog(syslog.LOG_INFO, "Script support_wlan_exceptions no pattern match - exiting script")
        sys.exit()