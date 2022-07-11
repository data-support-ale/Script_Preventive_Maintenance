#!/usr/local/bin/python3.7

import sys
import os
import json
import re
from time import strftime, localtime
from support_tools_OmniSwitch import get_credentials, collect_command_output_stp, check_save, add_new_save
from support_send_notification import *
from database_conf import *
import syslog

syslog.openlog('support_switch_stp')
syslog.syslog(syslog.LOG_INFO, "Executing script")


runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]

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
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
        print(msg)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog IP Address: " + ipadd)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog Hostname: " + host)
        #syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + msg)
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_stp.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_stp.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_stp.json - Error in regex")
        exit()
    try:
        vlan = re.findall(r"vlan (.*?) may not be stp enabled", msg)[0]
    except IndexError:
            # Log sample: Jun 21 14:13:38 OS6860E-P24-Building7 swlogd stpCmm _VLNt ALRM: stpCMM_handleVmMsg@1323->Some vlans between 68-73 may not be stp enabled
            try:
                vlan = re.findall(r"Some vlans between (.*?) may not be stp enabled", msg)[0]
            except IndexError:
                print("File /var/log/devices/lastlog_stp.json - Error in regex")
                syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_stp.json - Error in regex")

# always 1
#never -1
# ? 0
syslog.syslog(syslog.LOG_INFO, "Executing function check_save")
save_resp = check_save(ipadd, vlan, "stp")


if save_resp == "0":
    syslog.syslog(syslog.LOG_INFO, "No decision saved")
    if "may not be stp" in msg:
        decision = 0
        notif = ("Spanning Tree is running per-vlan mode on OmniSwitch {0} / {1} and following SpanTree VLAN {2} is disabled.\nDo you want to enable STP on this VLAN?").format(host,ipadd,vlan)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
        answer = send_message_request(notif, jid)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
    if answer == "2":
        add_new_save(ipadd, vlan, "stp", choice="always")
        syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " VLAN: " + vlan + " Choice: " + " Always")

    elif answer == "0":
        add_new_save(ipadd, vlan, "stp", choice="never")
        syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " VLAN: " + vlan + " Choice: " + " Never")
elif save_resp == "-1":
    try:
        syslog.syslog(syslog.LOG_INFO, "Decision saved to No - script exit")
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "VLAN": vlan}, "fields": {"count": 1}}])
        syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        sys.exit()   
    except UnboundLocalError as error:
       print(error)
       sys.exit()
    except Exception as error:
       print(error)
       sys.exit() 

elif save_resp == "1":
    answer = '2'
    print("Decision saved to Yes and remember")
    syslog.syslog(syslog.LOG_INFO, "Decision saved to Yes and remember")
else:
    answer = '1'
    syslog.syslog(syslog.LOG_INFO, "No answer - Decision set to Yes - Script exit - will be called by next occurence")    

syslog.syslog(syslog.LOG_INFO, "Rainbow Acaptive Card answer: " + answer)

if answer == '1':
    syslog.syslog(syslog.LOG_INFO, "Decision set to Yes - We disable the PoE on port")

    decision = "1"
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_stp")
    filename_path, subject, action, result, category = collect_command_output_stp(switch_user, switch_password, decision, host, ipadd, vlan)
    syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
    syslog.syslog(syslog.LOG_INFO, "Action: " + action)
    syslog.syslog(syslog.LOG_INFO, "Result: " + result)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")            
    send_file(filename_path, subject, action, result, category, jid)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

    try:
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "VLAN": vlan}, "fields": {"count": 1}}])
        syslog.syslog(syslog.LOG_INFO, "Statistics saved")
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