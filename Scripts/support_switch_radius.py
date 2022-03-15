#!/usr/local/bin/python3.7

import sys
import os
import json
import re
from time import strftime, localtime
from support_tools_OmniSwitch import get_credentials
from support_send_notification import send_message
from database_conf import *

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

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
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_radius_down.json empty")
        exit()
    # Sample log
    # swlogd radCli main INFO: RADIUS Primary Server - UPAM_Radius_Server is DOWN
    if "RADIUS Primary Server" in msg:
        try:
            radius_server, status = re.findall(r"RADIUS Primary Server - (.*?) is (.*)", msg)[0]
            info = "The Primary Radius Server " + radius_server + " set on the OmniSwitch " + host + "\" IP: " + ipadd + " aaa settings is " + status
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "Radius_Server": radius_server, "Status": status}, "fields": {"count": 1}}])
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
            radius_server, status = re.findall(r"RADIUS Backup Server - (.*?) is (.*)", msg)[0]
            info = "The Primary Radius Server " + radius_server + " set on the OmniSwitch " + host + "\" IP: " + ipadd + " aaa settings is " + status
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "Radius_Server": radius_server, "Status": status}, "fields": {"count": 1}}])
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
