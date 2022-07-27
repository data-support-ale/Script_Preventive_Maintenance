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

switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company, room_id = get_credentials()

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

            set_portnumber("0")
            set_decision(ipadd, "4")
            if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
                print("Less than 5 min")
                exit(0)

            os.system('logger -t montag -p user.info target asserted detected')
            subject = ("Preventive Maintenance Application - There is a Target Asserted error detected on server {0} from WLAN Stellar AP: {1}").format(ip_server, ipadd)
            action = "There is high probability that WLAN Stellar AP is rebooting following this exception"
            result = "This is a known issue fixed in AWOS 4.0.0 MR-3, more details in the Technical Knowledge Base https://myportal.al-enterprise.com/alebp/s/tkc-redirect?000058976"
            send_alert(subject, action, result)
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()

        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=subject, exception='')
        sys.exit(0)

    # Sample log for Internal Error Exception
    # [00001000] *pgd=00000000<4><0>Internal error: Oops: 17 [#1] PREEMPT SMP ARM
    elif "Internal error" in msg:
        try:

            set_portnumber("0")
            set_decision(ipadd, "4")
            if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
                print("Less than 5 min")
                exit(0)

            os.system('logger -t montag -p user.info internal error detected')
            subject = ("Preventive Maintenance Application - There is an Internal Error detected on server {0} from WLAN Stellar AP: {1}").format(ip_server, ipadd)
            action = "There is high probability that WLAN Stellar AP is rebooting following this exception"
            result = "If WLAN Stellar AP is running AWOS 3.0.7 there is a known issue related to IPv6, more details in the Technical Knowledge Base https://myportal.al-enterprise.com/alebp/s/tkc-redirect?000056737"
            send_alert(subject, action, result)
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()

        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=subject, exception='')
        sys.exit(0)

    # Sample log for Kernel panic
    # <0>Kernel panic - not syncing: Fatal exception in interrupt
    elif "Kernel panic" or "Fatal exception" or "KERNEL PANIC" in msg:
        try:

            set_portnumber("0")
            set_decision(ipadd, "4")
            if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
                print("Less than 5 min")
                exit(0)

            os.system('logger -t montag -p user.info Kernel Panic detected')
            subject = ("Preventive Maintenance Application - There is a Kernel Panic error detected on server {0} from WLAN Stellar AP: {1}").format(ip_server, ipadd)
            action = "There is high probability that WLAN Stellar AP is rebooting following this exception"
            result = "This is a known issue fixed in AWOS 4.0.4 MR-4, more details in the Technical Knowledge Base https://myportal.al-enterprise.com/alebp/s/tkc-redirect?000067381"
            send_alert(subject, action, result)
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()

        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=subject, exception='')
        sys.exit(0)

    # Sample log for Fatal exception
    # <0>Kernel panic - not syncing: Fatal exception in interrupt
    elif "Exception stack" or "core-monitor reboot" or "parse condition rule is error" in msg:
        try:
 
            set_portnumber("0")
            set_decision(ipadd, "4")
            if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
                print("Less than 5 min")
                exit(0)
 
            os.system('logger -t montag -p user.info Kernel Panic detected')
            subject = ("Preventive Maintenance Application - An unhandled exception occurred on server {0} from WLAN Stellar AP: {1}").format(ip_server, ipadd)
            action = "There is high probability that WLAN Stellar AP is rebooting following this exception"
            result = "Please contact ALE Customer Support"
            send_alert(subject, action, result)
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()

        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=subject, exception='')
        sys.exit(0)

    else:
        print("Script support_wlan_exceptions no pattern match - exiting script")
        sys.exit()
