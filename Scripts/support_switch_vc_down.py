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

syslog.openlog('support_switch_vc_down')
syslog.syslog(syslog.LOG_INFO, "Executing script")

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

last = ""
with open("/var/log/devices/lastlog_vc_down.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_vc_down.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_vc_down.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
        print(msg)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog IP Address: " + ipadd)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog Hostname: " + host)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + msg)
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_vc_down.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_vc_down.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_vc_down.json - Index error in regex")
        exit()
    # Sample log
    # swlogd: ChassisSupervisor bootMgr info(5) bootMgrVCMTopoDataEventHandler: remote chassis 3 no longer in the topology - closing
    if "bootMgrVCMTopoDataEventHandler" in msg:
        try:
            pattern = "bootMgrVCMTopoDataEventHandler"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            nb_vc = re.findall(r"bootMgrVCMTopoDataEventHandler: remote chassis (.*?) no longer in the topology", msg)[0]
            notif = ("Preventive Maintenance Application - The Virtual Chassis Unit {0} of OmniSwitch {1} / {2} is DOWN.\nRemote Chassis no longer in the topology.").format(nb_vc,host,ipadd)
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send notification")
            send_message(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "VC_Unit_Down": nb_vc}, "fields": {"count": 1}}])
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
    # swlogd intfCmm Mgr INFO: cmmEsmHandleNIDown: Rxed CSLIB_EVENT_NIDOWN event for chassis=2 slot=1, module=101065220
    elif "cmmEsmHandleNIDown" in msg:
        try:
            pattern = "cmmEsmHandleNIDown"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            nb_vc = re.findall(r"CSLIB_EVENT_NIDOWN event for chassis=(.*?) slot", msg)[0]
            notif = ("Preventive Maintenance Application - The Virtual Chassis Unit {0} of OmniSwitch {1} / {2} is DOWN.\nWe received NI Down event from this unit.").format(nb_vc,host,ipadd)
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send notification")
            send_message(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "VC_Unit_Down": nb_vc}, "fields": {"count": 1}}])
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
    # swlogd ChassisSupervisor bootMgr EVENT: CUSTLOG CMM Sending VC Takeover to NIs and applications
    elif "VC Takeover" in msg:
        pattern = "VC Takeover"
        syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
        notif = ("Preventive Maintenance Application - The Virtual Chassis Unit of OmniSwitch {0} / {1} is doing a TakeOver.").format(host,ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send notification")
        send_message(notif, jid)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

        try:
            write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "VC_Unit_Down": "TakeOver"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass 
    # Sample log
    # swlogd ChassisSupervisor MipMgr EVENT: CUSTLOG CMM The switch was restarted by the user
    # swlogd ChassisSupervisor MipMgr EVENT: CUSTLOG CMM The switch was restarted by a power cycle or due to some type of failure
    elif "The switch was restarted by" in msg:
        try:
            pattern = "The switch was restarted by"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            reason = re.findall(r"The switch was restarted by (.*)", msg)[0]
            notif = ("Preventive Maintenance Application - The Virtual Chassis Unit of OmniSwitch {0} / {1} is reloading by {2}.").format(host,ipadd,reason)
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send notification")
            send_message(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "VC_Unit_Down": "Reload", "Reason": reason}, "fields": {"count": 1}}])
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
