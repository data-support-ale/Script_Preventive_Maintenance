#!/usr/local/bin/python3.7

import sys
import os
import json
import re
from time import strftime, localtime
from datetime import datetime, timedelta
from support_tools_OmniSwitch import get_credentials, collect_command_output_health_port, collect_command_output_health_memory, collect_command_output_health_cpu, send_file, get_tech_support_sftp
from support_send_notification import send_message
from database_conf import *

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]
logging = "logger -t montag -p user.info Executing script {0}".format(script_name)
try:
    os.system('logger -t montag -p user.info ' + logging)
except:
    pass

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()
last = ""
with open("/var/log/devices/lastlog_switch_health.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_switch_health.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_switch_health.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
        print(msg)
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_switch_health.json empty")
        exit()
    # Sample log
    # {"@timestamp":"2021-11-22T21:57:06+01:00","type":"syslog_json","relayip":"10.130.7.243","hostname":"sw5-bcb","message":"<134>Nov 22 21:57:06 OS6860E_VC_Core swlogd healthCmm main EVENT: CUSTLOG CMM NI 1/1 rising above CPU threshold","end_msg":""}
    if "CMM NI" in msg:
        try:
            pattern = "CMM NI"
            logging = "logger -t montag -p user.info Executing script {0} - pattern detected: {1}".format(script_name,pattern)
            try:
                os.system('logger -t montag -p user.info ' + logging)
            except:
                pass
            nb_vc, topic = re.findall(r"CMM NI (.*?) rising above (.*?) threshold", msg)[0]
            filename_path, subject, action, result, category = collect_command_output_health_cpu(switch_user, switch_password, host, ipadd)
#            get_tech_support_sftp(switch_user, switch_password, host, ipadd)
            send_file(filename_path, subject, action, result, category, jid)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Health": topic, "VC_Unit": nb_vc}, "fields": {"count": 1}}])
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
    # {"@timestamp":"2021-11-22T21:57:06+01:00","type":"syslog_json","relayip":"10.130.7.243","hostname":"sw5-bcb","message":"2021 Sep 13 07:39:00 cma-2a-6900-ale swlogd: ChassisSupervisor memMgr alert(3) WATERMARK_HIGH(2) The top 20 memory hogs in Zone High Memory(1) are ....","end_msg":""}
    elif "top 20 memory" in msg:
        try:
            pattern = "top 20 memory"
            logging = "logger -t montag -p user.info Executing script {0} - pattern detected: {1}".format(script_name,pattern)
            try:
                os.system('logger -t montag -p user.info ' + logging)
            except:
                pass
            filename_path, subject, action, result, category = collect_command_output_health_memory(switch_user, switch_password, host, ipadd)
            get_tech_support_sftp(switch_user, switch_password, host, ipadd)
            send_file(filename_path, subject, action, result, category, jid)
            print(log_file.readlines()[1])
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Health": "MEMORY"}, "fields": {"count": 1}}])
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
    # swlogd OS6860E_VC_Core swlogd healthCmm main EVENT: CUSTLOG CMM Port 1/1/15 rising above receive threshold
    elif "CMM Port" in msg:
        try:
            port, type = re.findall(r"CMM Port (.*?) rising above (.*?) threshold", msg)[0]
            filename_path, subject, action, result, category = collect_command_output_health_port(switch_user, switch_password, port, type, host, ipadd)
#            get_tech_support_sftp(switch_user, switch_password, host, ipadd)
            send_file(filename_path, subject, action, result, category, jid)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Health": "PORT", "Port": port, "Type": type}, "fields": {"count": 1}}])
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