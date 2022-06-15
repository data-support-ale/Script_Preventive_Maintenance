#!/usr/local/bin/python3.7

import sys
import os
import re
import json
from support_tools_OmniSwitch import get_credentials
from time import strftime, localtime, sleep
from support_send_notification import send_message_request
from database_conf import *
from support_tools_OmniSwitch import add_new_save, check_save, send_file

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()
agg_id = "0"
last = ""
with open("/var/log/devices/lastlog_violation.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_violation.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_violation.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ip = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_violation.json empty")
        exit()
    except IndexError:
        print("Index error in regex")
        exit()
    # Sample log
    # swlogd portMgrNi main INFO: : [pmNiHandleNonUniqueViolation:779] Violation on Gport 0x20026 which is part of Lag 33554471 New Violation Set on Lag Port
    # swlogd portMgrNi main INFO: : [pmNiHandleNonUniqueViolation:779] Violation on Gport 0x2 which is part of Lag 33554433 New Violation Set on Lag Port

    if "New Violation Set on Lag Port" in msg:
        try:
            port, agg_id = re.findall(r"Violation on Gport (.*?) which is part of Lag (.*?) New Violation Set on Lag Port", msg)[0]
            agg_id=int(agg_id)
            reason = "LBD"
            # 
            agg_id=hex(agg_id)
            print(agg_id)
            n = len(str(agg_id))
            print(n)
            dig = []
            dig = list(agg_id for agg_id in str(agg_id))
            if str(dig[7]) == "0":
               agg_id = str(dig[8])
            else:
                agg_id = dig[7] + dig[8]
                # if 2 digits we have to convert from hexa to decimal

            print(agg_id)
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError:
            print("Index error in regex")
            exit()
    
    # Sample log
    # swlogd portMgrCmm main EVENT: CUSTLOG CMM Port 2\/1\/46 in violation - source 10 reason Not a recovery reason"
    elif "in violation" in msg:
        try:
            port, reason = re.findall(r"Port (.*?) in violation - source (.*?) reason", msg)[0]
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError:
            print("Index error in regex")
            exit()

        if reason == "0":
            reason = "Unknown"
        elif reason == "1":
            reason = "Access Guardian"
        elif reason == "2":
            reason = "QOS Policy"
        elif reason == "3":
            reason = "Net Sec"
        elif reason == "4":
            reason = "UDLD"
        elif reason == "5":
            reason = "NI supervision (Fabric Stability)"
        elif reason == "6":
            reason = "OAM"
        elif reason == "8":
            reason = "LFP"
        elif reason == "9":
            reason = "Link monitoring"
        elif reason == "10":
            reason = "LBD"
        elif reason == "11":
            reason = "SPB"
        elif reason == "12":
            reason = "ESM"
        elif reason == "13":
            reason = "ESM"
        elif reason == "14":
            reason = "LLDP"

    else:
        print("no pattern match - exiting script")
        sys.exit()

# always 1
#never -1
# ? 0
save_resp = check_save(ip, port, "violation")

if save_resp == "0":
    if agg_id == "0":
        notif = "A port violation occurs on OmniSwitch " + host + " port " + port + ", source: " + reason + ". Do you want to clear the violation? " + ip_server
        answer = send_message_request(notif, jid)
        print(answer)
        if answer == "2":
            add_new_save(ip, port, "violation", choice="always")
        elif answer == "0":
            add_new_save(ip, port, "violation", choice="never")
    else:
        notif = "A port violation occurs on OmniSwitch " + host + " LinkAgg ID " + agg_id + ", source: " + reason + ". Do you want to clear the violation? " + ip_server
        answer = send_message_request(notif, jid)
        print(answer)
        if answer == "2":
            add_new_save(ip, port, "violation", choice="always")
        elif answer == "0":
            add_new_save(ip, port, "violation", choice="never")

elif save_resp == "-1":
    try:
        print(port)
        print(reason)
        print(ip)
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ip, "Reason": reason, "port": port}, "fields": {"count": 1}}])
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
    os.system('logger -t montag -p user.info Process terminated')
    # CLEAR VIOLATION
    cmd = "clear violation port " + port
    os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user, ip, cmd))
    ## 2 seconds delay for getting port violation logs
    sleep(2)
    filename_path = "/var/log/devices/" + host + "/syslog.log"
    category = "port_violation"
    subject = "A port violation is detected:".format(host, ip)
    action = "Violation on OmniSwitch {0}, port {1} has been cleared up".format(host, port)
    result = "Find enclosed to this notification the log collection"
    send_file(filename_path, subject, action, result, category, jid)

elif answer == '2':
    os.system('logger -t montag -p user.info Process terminated')
    # CLEAR VIOLATION
    cmd = "clear violation port " + port
    os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
        switch_password, switch_user, ip, cmd))

else:
    print("Mail request set as no")
    os.system('logger -t montag -p user.info Mail request set as no')
    sleep(1)

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                    "IP": ip, "Reason": reason, "port": port}, "fields": {"count": 1}}])
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass 
