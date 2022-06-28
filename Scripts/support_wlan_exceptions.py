#!/usr/bin/env python3

import sys
import os
from time import strftime, localtime
import re
from support_tools_OmniSwitch import get_credentials
from support_send_notification import *
import json
import time

##### To Add in rsyslog.conf #####
#template (name="wlanlogexceptions" type="string"
#     string="/var/log/devices/lastlog_wlan_exceptions.json")

#if $msg contains 'TARGET ASSERTED' then {
#     $RepeatedMsgReduction on
#     action(type="omfile" DynaFile="wlanlogexceptions" template="json_syslog" DirCreateMode="0755" FileCreateMode="0755")
#     action(type="omprog" name="support_wlan_generic_exceptions" binary="/opt/preventive-maintenance-2.1.8/ALE_v2/ale_scripts/support_wlan_exceptions.py \"TARGET ASSERTED\"")
#     stop
#}

#if $msg contains 'Internal error' then {
#     $RepeatedMsgReduction on
#     action(type="omfile" DynaFile="wlanlogexceptions" template="json_syslog" DirCreateMode="0755" FileCreateMode="0755")
#     action(type="omprog" name="support_wlan_generic_exceptions" binary="/opt/preventive-maintenance-2.1.8/ALE_v2/ale_scripts/support_wlan_exceptions.py \"Internal error\"")
#     stop
#}

#if $msg contains 'Fatal exception' or $msg contains 'Kernel panic' or $msg contains 'KERNEL PANIC' or $msg contains 'Exception stack' or $msg contains 'parse condition rule is error' or $m>
#     $RepeatedMsgReduction on
#     action(type="omfile" DynaFile="wlanlogexceptions" template="json_syslog" DirCreateMode="0755" FileCreateMode="0755")
#     action(type="omprog" name="support_wlan_generic_exception" binary="/opt/preventive-maintenance-2.1.8/ALE_v2/ale_scripts/support_wlan_exceptions.py \"Fatal exception;or;Kernel panic;or>
#     stop
#}

#if $msg contains 'Unable to handle kernel' then {
#     $RepeatedMsgReduction on
#     action(type="omfile" DynaFile="wlanlogexceptions" template="json_syslog" DirCreateMode="0755" FileCreateMode="0755")
#     action(type="omprog" binary="/opt/preventive-maintenance-2.1.8/ALE_v2/ale_scripts/support_wlan_exceptions.py  \"Unable to handle kernel\"")
#     stop
#}

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))

_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)

switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

last = ""
with open("/var/log/devices/lastlog_wlan_exceptions.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_wlan_exceptions.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_wlan_exceptions.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_wlan_exceptions.json empty")
        exit()
    # Sample log for TARGET ASSERTED Exception
    # [wifi0][0x0000000B]: XXX TARGET ASSERTED XXX
    if "TARGET ASSERTED" in msg:
        try:
            os.system('logger -t montag -p user.info target asserted detected')
            subject = ("Preventive Maintenance Application - There is a Target Asserted error detected on server {0} from WLAN Stellar AP: {1}").format(ip_server, ipadd)
            action = "There is high probability that WLAN Stellar AP is rebooting following this exception"
            result = "This is a known issue fixed in AWOS 4.0.0 MR-3, more details in the Technical Knowledge Base https://myportal.al-enterprise.com/alebp/s/tkc-redirect?000058976"
            filename_path = "/var/log/devices/lastlog_wlan_exceptions.json"
            category = "TARGET_ASSERTED"
            send_file(filename_path, subject, action, result, category, jid)
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
        sys.exit(0)

    # Sample log for Internal Error Exception
    # [00001000] *pgd=00000000<4><0>Internal error: Oops: 17 [#1] PREEMPT SMP ARM
    elif "Internal error" in msg:
        try:
            os.system('logger -t montag -p user.info internal error detected')
            subject = ("Preventive Maintenance Application - There is an Internal Error detected on server {0} from WLAN Stellar AP: {1}").format(ip_server, ipadd)
            action = "There is high probability that WLAN Stellar AP is rebooting following this exception"
            result = "If WLAN Stellar AP is running AWOS 3.0.7 there is a known issue related to IPv6, more details in the Technical Knowledge Base https://myportal.al-enterprise.com/alebp/s/tkc-redirect?000056737"
            filename_path = "/var/log/devices/lastlog_wlan_exceptions.json"
            category = "Internal_error"
            send_file(filename_path, subject, action, result, category, jid)
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
        sys.exit(0)

    # Sample log for Kernel panic
    # <0>Kernel panic - not syncing: Fatal exception in interrupt
    elif "Kernel panic" or "Fatal exception" or "KERNEL PANIC" in msg:
        try:
            os.system('logger -t montag -p user.info Kernel Panic detected')
            subject = ("Preventive Maintenance Application - There is a Kernel Panic error detected on server {0} from WLAN Stellar AP: {1}").format(ip_server, ipadd)
            action = "There is high probability that WLAN Stellar AP is rebooting following this exception"
            result = "This is a known issue fixed in AWOS 4.0.4 MR-4, more details in the Technical Knowledge Base https://myportal.al-enterprise.com/alebp/s/tkc-redirect?000067381"
            filename_path = "/var/log/devices/lastlog_wlan_exceptions.json"
            category = "Exception"
            send_file(filename_path, subject, action, result, category, jid)
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
        sys.exit(0)

    # Sample log for Fatal exception
    # <0>Kernel panic - not syncing: Fatal exception in interrupt
    elif "Exception stack" or "core-monitor reboot" or "parse condition rule is error" in msg:
        try:
            os.system('logger -t montag -p user.info Kernel Panic detected')
            subject = ("Preventive Maintenance Application - An unhandled exception occurred on server {0} from WLAN Stellar AP: {1}").format(ip_server, ipadd)
            action = "There is high probability that WLAN Stellar AP is rebooting following this exception"
            result = "Please contact ALE Customer Support"
            filename_path = "/var/log/devices/lastlog_wlan_exceptions.json"
            category = "Exception"
            send_file(filename_path, subject, action, result, category, jid)
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()

    # Kernel exception
    elif "Unable to handle kernel" in msg:
        try: 
            os.system('logger -t montag -p user.info Kernel Panic detected')
            subject = ("Preventive Maintenance Application - An unhandled exception occurred on server {0} from WLAN Stellar AP: {1}").format(ip_server, ipadd)
            action = "There is high probability that WLAN Stellar AP is rebooting following this exception"
            result = "Please contact ALE Customer Support"
            filename_path = "/var/log/devices/lastlog_wlan_exceptions.json"
            category = "Exception"
            send_file(filename_path, subject, action, result, category, jid)
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
        sys.exit(0)

    else:
        print("Script support_wlan_exceptions no pattern match - exiting script")
        sys.exit()