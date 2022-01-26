#!/usr/bin/env python

import sys
import os
import json
import re
from time import strftime, localtime
from support_tools_OmniSwitch import get_credentials
from support_send_notification import send_message
from database_conf import *

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

switch_user,switch_password,mails,jid,ip_server,login_AP,pass_AP,tech_pass,random_id,company = get_credentials()

last = ""
with open("/var/log/devices/lastlog_vc_down.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_vc_down.json","w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_vc_down.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_vc_down.json empty")
        exit()
    # Sample log 
    # swlogd: ChassisSupervisor bootMgr info(5) bootMgrVCMTopoDataEventHandler: remote chassis 3 no longer in the topology - closing
    if "bootMgrVCMTopoDataEventHandler" in msg:
        try:
            nb_vc = re.findall(r"bootMgrVCMTopoDataEventHandler: remote chassis (.*?) no longer in the topology", msg)[0]
            info = "The Virtual Chassis Unit " + nb_vc + " of OmniSwitch \"" + host + "\" IP: " + ipadd + " is DOWN"
            send_message(info,jid)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "VC_Unit_Down": nb_vc}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
    #Sample log
    #swlogd intfCmm Mgr INFO: cmmEsmHandleNIDown: Rxed CSLIB_EVENT_NIDOWN event for chassis=2 slot=1, module=101065220
    elif "cmmEsmHandleNIDown" in msg:
        try:
            nb_vc = re.findall(r"CSLIB_EVENT_NIDOWN event for chassis=(.*?) slot", msg)[0]
            info = "The Virtual Chassis Unit " + nb_vc + " of OmniSwitch \"" + host + "\" IP: " + ipadd + " is DOWN"
            send_message(info,jid)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "VC_Unit_Down": nb_vc}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
    #Sample log
    #swlogd ChassisSupervisor bootMgr EVENT: CUSTLOG CMM Sending VC Takeover to NIs and applications
    elif "VC Takeover" in msg:
        info = "The Virtual Chassis \"" + host + "\" IP: " + ipadd + " is doing a TakeOver"
        send_message(info,jid)
        try:
            write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "VC_Unit_Down": "TakeOver"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
    #Sample log
    #swlogd ChassisSupervisor MipMgr EVENT: CUSTLOG CMM The switch was restarted by the user
    #swlogd ChassisSupervisor MipMgr EVENT: CUSTLOG CMM The switch was restarted by a power cycle or due to some type of failure
    elif "The switch was restarted by" in msg:
        try:
            reason = re.findall(r"The switch was restarted by (.*)", msg)[0]
            info = "The Virtual Chassis \"" + host + "\" IP: " + ipadd + " did reload by " + reason
            print(info)
            send_message(info,jid)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "VC_Unit_Down": "Reload", "Reason": reason}, "fields": {"count": 1}}])
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

open('/var/log/devices/lastlog_vc_down.json','w').close()

