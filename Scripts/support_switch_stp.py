#!/usr/local/bin/python3.7

import sys
import os
import json
import re
from time import strftime, localtime
from support_tools_OmniSwitch import get_credentials, collect_command_output_stp, check_save, send_file, add_new_save
from support_send_notification import send_message, send_message_request
from database_conf import *

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

# Sample log
# swlogd stpCmm _VLNt ALRM: stpCMM_handleVmMsg@1319->vlan 531 may not be stp enabled

last = ""
with open("/var/log/devices/lastlog_stp.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_stp.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_stp.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ip = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_stp.json empty")
        exit()
    except IndexError:
        print("Index error in regex")
        exit()
    try:
        vlan = re.findall(r"vlan (.*?) may not be stp enabled", msg)[0]
    except IndexError:
        print("Index error in regex")
        exit()

# always 1
#never -1
# ? 0
save_resp = check_save(ip, vlan, "stp")


if save_resp == "0":
    if "may not be stp" in msg:
        notif = "Spanning Tree is running per-vlan mode and following VLAN: " + vlan + " is disabled on OmniSwitch " + host + ". Do you want to enable STP on this VLAN?" + ip_server        #send_message(info, jid)
        answer = send_message_request(notif, jid)
        print(answer)
        filename_path, subject, action, result, category = collect_command_output_stp(switch_user, switch_password, host, ip, vlan)
        send_file(filename_path, subject, action, result, category)
    if answer == "2":
        add_new_save(ip, vlan, "stp", choice="always")
    elif answer == "0":
        add_new_save(ip, vlan, "stp", choice="never")
elif save_resp == "-1":
    try:
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ip, "VLAN": vlan}, "fields": {"count": 1}}])
        sys.exit()   
    except UnboundLocalError as error:
       print(error)
       sys.exit()

elif save_resp == "1":
    answer = '2'
else:
    answer = '1'

if answer == '1':
        filename_path, subject, action, result, category = collect_command_output_stp(switch_user, switch_password, host, ip, vlan)
        send_file(filename_path, subject, action, result, category)
        try:
           write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ip, "VLAN": vlan}, "fields": {"count": 1}}])
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
    print("no pattern match - exiting script")
    sys.exit()