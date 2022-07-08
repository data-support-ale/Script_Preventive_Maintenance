#!/usr/local/bin/python3.7

import sys
import os
import json
import re
from time import strftime, localtime
from support_tools_OmniSwitch import get_credentials
from support_send_notification import send_message
from database_conf import *
import syslog

syslog.openlog('support_switch_radius')
syslog.syslog(syslog.LOG_INFO, "Executing script")


runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

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
    # Sample log
    # swlogd radCli main INFO: RADIUS Primary Server - UPAM_Radius_Server is DOWN
    if "RADIUS Primary Server" in msg:
        try:
            pattern = "RADIUS Primary Server"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            radius_server, status = re.findall(r"RADIUS Primary Server - (.*?) is (.*)", msg)[0]
            notif = "The Primary Radius Server " + radius_server + " set on the OmniSwitch " + host + "\" IP: " + ipadd + " aaa settings is " + status
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
            send_message(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Radius_Server": radius_server, "Status": status}, "fields": {"count": 1}}])
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
    # swlogd radCli main INFO: RADIUS Backup Server - UPAM_Radius_Server is DOWN
    elif "RADIUS Backup Server" in msg:
        try:
            pattern = "RADIUS Primary Server"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            radius_server, status = re.findall(r"RADIUS Backup Server - (.*?) is (.*)", msg)[0]
            notif = ("Preventive Maintenance Application - The Primary Radius Server{0} set on the OmniSwitch {1} / {2} aaa settings is {3}").format(radius_server,host,ipadd,status)
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
            send_message(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Radius_Server": radius_server, "Status": status}, "fields": {"count": 1}}])
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
        print("No pattern match - exiting script")
        syslog.syslog(syslog.LOG_INFO, "No pattern match - exiting script")
        sys.exit()
