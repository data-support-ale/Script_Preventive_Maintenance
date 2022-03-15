#!/usr/local/bin/python3.7

import sys
import os
import json
from time import strftime, localtime
from support_tools_OmniSwitch import get_credentials, send_file, collect_command_output_ps
from support_send_notification import send_message
from database_conf import *
import re

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

last = ""
with open("/var/log/devices/lastlog_power_supply_down.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_power_supply_down.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_power_supply_down.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_power_supply_down.json empty")
        exit()
    except IndexError:
        print("Index error in regex")
        exit()

    # Sample log
    # OS6860E swlogd ChassisSupervisor Power Mgr INFO: Power Supply 1 Removed
    if "Removed" in msg:
        try:
            nb_power_supply = re.findall(r"Power Supply (.*?) Removed", msg)[0]
            filename_path, subject, action, result, category = collect_command_output_ps(switch_user, switch_password, nb_power_supply, host, ipadd)
            send_file(filename_path, subject, action, result, category)
#            info = "A default on Power supply {} from device {} has been detected".format(nb_power_supply, ipadd)
#            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "PS_Unit": nb_power_supply}, "fields": {"count": 1}}])
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
    # OS6860E swlogd ChassisSupervisor MipMgr EVENT: CUSTLOG CMM chassisTrapsAlert - Power supply is inoperable: PS 2
    elif "inoperable" in msg:
        try:
            nb_power_supply = re.findall(r"Power supply is inoperable: PS (.*)", msg)[0]
            filename_path, subject, action, result, category = collect_command_output_ps(switch_user, switch_password, nb_power_supply, host, ipadd)
            send_file(filename_path, subject, action, result, category)
#            info = "A default on Power supply {} from device {} has been detected".format(nb_power_supply, ipadd)
#            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "PS_Unit": nb_power_supply}, "fields": {"count": 1}}])
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
    # OS6860E swlogd ChassisSupervisor MipMgr EVENT: CUSTLOG CMM Device Power Supply operational state changed to UNPOWERED
    elif "UNPOWERED" in msg:
        try:
            nb_power_supply = "Unknown"
            filename_path, subject, action, result, category = collect_command_output_ps(switch_user, switch_password, nb_power_supply, host, ipadd)
            send_file(filename_path, subject, action, result, category)
#            info = "A default on Power supply \"Power Supply operational state changed to UNPOWERED\" from device {} has been detected".format(ipadd)
#            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename( __file__)), "tags": {"IP": ipadd, "PS_Unit": "All"}, "fields": {"count": 1}}])
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
