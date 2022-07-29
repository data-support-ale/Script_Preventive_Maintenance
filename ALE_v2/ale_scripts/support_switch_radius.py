#!/usr/bin/env python3

import sys
import os
import json
import re
from time import strftime, localtime
from support_tools_OmniSwitch import get_credentials
from support_send_notification import *
# from database_conf import *
import time
import syslog

syslog.openlog('support_switch_radius')
syslog.syslog(syslog.LOG_INFO, "Executing script")


from pattern import set_rule_pattern, set_portnumber, set_decision, mysql_save

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

pattern = sys.argv[1]
print(pattern)
set_rule_pattern(pattern)

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company, room_id = get_credentials()

last = ""
with open("/var/log/devices/lastlog_radius_down.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_radius_down.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_radius_down.json", "r", errors='ignore') as log_file:
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
        print("File /var/log/devices/lastlog_radius_down.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_radius_down.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_radius_down.json - Index error in regex")
        exit()
    syslog.syslog(syslog.LOG_INFO, "Executing function set_portnumber 0")
    set_portnumber("0")
    if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
        print("Less than 5 min")
        syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
        exit(0)

    # Sample log
    # swlogd radCli main INFO: RADIUS Primary Server - UPAM_Radius_Server is DOWN
    if "RADIUS Primary Server" in msg:
        try:
            pattern = "RADIUS Primary Server"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            radius_server, status = re.findall(r"RADIUS Primary Server - (.*?) is (.*)", msg)[0]
            notif = "The Primary Radius Server " + radius_server + " set on the OmniSwitch " + host + "\" IP: " + ipadd + " aaa settings is " + status
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Sending notification")
            send_message(notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            try:
                set_decision(ipadd, "4")
                mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
                syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision") 
            except UnboundLocalError as error:
                print(error)
                sys.exit()
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
    # Sample log
    # swlogd radCli main INFO: RADIUS Backup Server - UPAM_Radius_Server is DOWN
    elif "RADIUS Backup Server" in msg:
        try:
            pattern = "RADIUS Primary Server"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            radius_server, status = re.findall(r"RADIUS Backup Server - (.*?) is (.*)", msg)[0]
            notif = ("Preventive Maintenance Application - The Primary Radius Server{0} set on the OmniSwitch {1} / {2} aaa settings is {3}").format(radius_server,host,ipadd,status)
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
            send_message(notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            try:
                set_decision(ipadd, "4")
                mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
                syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision") 
            except UnboundLocalError as error:
                print(error)
                sys.exit()
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
    else:
        print("No pattern match - exiting script")
        syslog.syslog(syslog.LOG_INFO, "No pattern match - exiting script")
        sys.exit()
