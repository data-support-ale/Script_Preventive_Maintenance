#!/usr/local/bin/python3.7

import sys
import os
import re
import json
from support_tools_OmniSwitch import get_credentials, ssh_connectivity_check
from time import strftime, localtime, sleep
from support_send_notification import *
from database_conf import *
from support_tools_OmniSwitch import add_new_save, check_save, send_file
import syslog

syslog.openlog('support_switch_violation')
syslog.syslog(syslog.LOG_INFO, "Executing script")


runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]

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
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
        print(msg)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog IP Address: " + ipadd)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog Hostname: " + host)
        #syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + msg)
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_violation.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_violation.jso - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_violation.jso - Index error in regex")
        exit()
    # Sample log
    # swlogd portMgrNi main INFO: : [pmNiHandleNonUniqueViolation:779] Violation on Gport 0x20026 which is part of Lag 33554471 New Violation Set on Lag Port
    # swlogd portMgrNi main INFO: : [pmNiHandleNonUniqueViolation:779] Violation on Gport 0x2 which is part of Lag 33554433 New Violation Set on Lag Port

    if "New Violation Set on Lag Port" in msg:
        try:
            pattern = "New Violation Set on Lag Port"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            port, agg_id = re.findall(r"Violation on Gport (.*?) which is part of Lag (.*?) New Violation Set on Lag Port", msg)[0]
            agg_id=int(agg_id)
            reason = "LBD"
            agg_id=hex(agg_id)
            syslog.syslog(syslog.LOG_INFO, "Aggregate ID in Hexa: " + agg_id)
            print(agg_id)
            n = len(str(agg_id))
            print(n)
            dig = []
            dig = list(agg_id for agg_id in str(agg_id))
            if str(dig[7]) == "0":
               agg_id = str(dig[8])
               syslog.syslog(syslog.LOG_INFO, "Port violation reason: LBD on LinkAgg/Port: " + agg_id + "/" + port)

            else:
                agg_id = dig[7] + dig[8]
                syslog.syslog(syslog.LOG_INFO, "Port violation reason: LBD on LinkAgg/Port: " + agg_id + "/" + port)

                # if 2 digits we have to convert from hexa to decimal

            print(agg_id)
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError:
            syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_violation.jso - Index error in regex - script exit")
            exit()
    
    # Sample log
    # swlogd portMgrCmm main EVENT: CUSTLOG CMM Port 2\/1\/46 in violation - source 10 reason Not a recovery reason"
    elif "in violation" in msg:
        pattern = "New Violation Set on Lag Port"
        syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
        try:
            port, reason = re.findall(r"Port (.*?) in violation - source (.*?) reason", msg)[0]
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError:
            syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_violation.jso - Index error in regex - script exit")
            exit()
        syslog.syslog(syslog.LOG_INFO, "Violation port and reason: " + port + " " + reason)
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
        syslog.syslog(syslog.LOG_INFO, "Violation port and reason: " + port + " " + reason)

    else:
        print("No pattern match - exiting script")
        syslog.syslog(syslog.LOG_INFO, "No pattern match - exiting script")
        sys.exit()

# always 1
#never -1
# ? 0
syslog.syslog(syslog.LOG_INFO, "Executing function check_save")
save_resp = check_save(ipadd, port, "violation")

if save_resp == "0":
    syslog.syslog(syslog.LOG_INFO, "No decision saved")
    if agg_id == "0":
        syslog.syslog(syslog.LOG_INFO, "Port is not member of a LinkAgg")
        feature = "Disable Port " + port
        notif = ("Preventive Maintenance Application - A port violation occurs on OmniSwitch {0} / {1}. Port : {2} - Source : {3}.\nDo you want to clear the violation or administratively disable the Interface/Port?").format(host,ipadd,port,reason)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card of type Advanced")
        answer = send_message_request_advanced(notif, jid,feature)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        if answer == "2":
            add_new_save(ipadd, port, "violation", choice="always")
            syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Port: " + port + " Choice: " + " Always")

        elif answer == "0":
            add_new_save(ipadd, port, "violation", choice="never")
            syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Port: " + port + " Choice: " + " Never")

    else:
        syslog.syslog(syslog.LOG_INFO, "Port is member of a LinkAgg")
        feature = "Disable port " + agg_id
        notif = "Preventive Maintenance Application - A port violation occurs on OmniSwitch " + host + " LinkAgg ID " + agg_id + ", source: " + reason + ".\nDo you want to clear the violation or administratively disable the Link Aggregate? " + ip_server
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card of type Advanced")
        answer = send_message_request_advanced(notif, jid,feature)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        if answer == "2":
            add_new_save(ipadd, port, "violation", choice="always")
            syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Port: " + port + " Choice: " + " Always")

        elif answer == "0":
            add_new_save(ipadd, port, "violation", choice="never")
            syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Port: " + port + " Choice: " + " Never")

elif save_resp == "-1":
    print("Decision saved to No - script exit")
    syslog.syslog(syslog.LOG_INFO, "Decision saved to No - script exit")
    try:
        print(port)
        print(reason)
        print(ipadd)
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Reason": reason, "port": port}, "fields": {"count": 1}}])
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
    syslog.syslog(syslog.LOG_INFO, "Anwser received is Yes")
    syslog.syslog(syslog.LOG_INFO, "Clearing port violation")
    # CLEAR VIOLATION
    cmd = "clear violation port " + port
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
    syslog.syslog(syslog.LOG_INFO, "Port violation cleared up")
    ## 2 seconds delay for getting port violation logs
    sleep(2)

    filename_path = "/var/log/devices/" + host + "/syslog.log"
    syslog.syslog(syslog.LOG_INFO, "Logs attached: " + filename_path)
    category = "port_violation"
    subject = "Preventive Maintenance Application - A port violation has been detected:".format(host, ipadd)
    action = "Violation on OmniSwitch {0}, port {1} has been cleared up".format(host, port)
    result = "Find enclosed to this notification the log collection"
    syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
    syslog.syslog(syslog.LOG_INFO, "Action: " + action)
    syslog.syslog(syslog.LOG_INFO, "Result: " + result)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
    send_file(filename_path, subject, action, result, category, jid)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

elif answer == '2':
    syslog.syslog(syslog.LOG_INFO, "Anwser received is Yes and Remember")
    syslog.syslog(syslog.LOG_INFO, "Clearing port violation")
    # CLEAR VIOLATION
    cmd = "clear violation port " + port
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
    syslog.syslog(syslog.LOG_INFO, "Port violation cleared up")
    ## 2 seconds delay for getting port violation logs
    sleep(2)

## Value 3 when we return advanced value like Disable port x/x/x
elif answer == '3':
    syslog.syslog(syslog.LOG_INFO, "Anwser received is " + feature)
    # DISABLE Port
    if agg_id == "0":
        syslog.syslog(syslog.LOG_INFO, "SSH Session for disabling port")
        cmd = "interfaces port " + port + " admin-state disable"
        ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
        syslog.syslog(syslog.LOG_INFO, "SSH Session closed")
    else: 
        syslog.syslog(syslog.LOG_INFO, "SSH Session for disabling linkagg")
        cmd = "linkagg lacp agg " + agg_id + " admin-state disable"
        ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
        syslog.syslog(syslog.LOG_INFO, "SSH Session closed")   
    filename_path = "/var/log/devices/" + host + "/syslog.log"
    category = "port_violation"
    subject = "Preventive Maintenance Application - A port violation has been detected:".format(host, ipadd)
    if agg_id == "0":
        action = "Port violation has been fixed by administratively disabling LinkAgg {0} on OmniSwitch {1} / {2}".format(agg_id, host, ipadd)
    else:
        action = "Port violation has been fixed by administratively disabling Interface/Port {0} on OmniSwitch {1} / {2}".format(port, host, ipadd)
    result = "Find enclosed to this notification the log collection"
    syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
    syslog.syslog(syslog.LOG_INFO, "Action: " + action)
    syslog.syslog(syslog.LOG_INFO, "Result: " + result)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
    send_file(filename_path, subject, action, result, category, jid)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

else:
    print("No answer match")
    syslog.syslog(syslog.LOG_INFO, "No answer match - script exit")
    sleep(1)

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Reason": reason, "port": port}, "fields": {"count": 1}}])
    syslog.syslog(syslog.LOG_INFO, "Statistics saved")
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass 
