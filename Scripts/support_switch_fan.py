#!/usr/local/bin/python3.7

import sys
import os
import re
import json
from support_tools_OmniSwitch import get_credentials, collect_command_output_fan,send_file,check_save,add_new_save
from time import strftime, localtime, sleep
from support_send_notification import send_message,send_message_request
from database_conf import *

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

# Log sample
# OS6860E_VC_Core swlogd swlogd ChassisSupervisor fan & temp Mgr ALRT: Chassis Fan Failure

last = ""
with open("/var/log/devices/lastlog_fan.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_fan.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_fan.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ip = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_fan.json empty")
        exit()
    except IndexError:
        print("Index error in regex")
        exit()

# always 1
#never -1
# ? 0
save_resp = check_save(ip, "1", "fan")



if save_resp == "0":
    if "Fan Failure" in msg:
        notif = "A FAN is inoperable on OmniSwitch " + host + ". Do you want to keep being notified? " + ip_server        #send_message(info, jid)
        answer = send_message_request(notif, jid)
        print(answer)
        if answer == "2":
            add_new_save(ip, "1", "fan", choice="always")
        elif answer == "0":
            add_new_save(ip, "1", "fan", choice="never")
        filename_path, subject, action, result, category, chassis_id = collect_command_output_fan(switch_user, switch_password, host, ip)
        send_file(filename_path, subject, action, result, category, jid)
elif save_resp == "-1":
    try:
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ip, "FAN_Unit_ID": " 1"}, "fields": {"count": 1}}])
        sys.exit()   
    except UnboundLocalError as error:
       print(error)
       sys.exit()
    except Exception as error:
        print(error)
        sys.exit() 

elif save_resp == "1":
    answer = '2'
else:
    answer = '1'

if answer == '1':
        filename_path, subject, action, result, category, chassis_id = collect_command_output_fan(switch_user, switch_password, host, ip)
        send_file(filename_path, subject, action, result, category, jid)
        try:
           write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ip, "FAN_Unit_ID": chassis_id}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass 
else:
    print("no pattern match - exiting script")
    sys.exit()
