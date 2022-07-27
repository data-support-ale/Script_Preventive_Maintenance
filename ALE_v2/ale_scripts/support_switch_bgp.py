#!/usr/bin/env python3

import sys
import os
import re
import syslog
import json
from support_tools_OmniSwitch import get_credentials
from time import strftime, localtime, sleep
from support_send_notification import *
# from database_conf import *
import time
import syslog

syslog.openlog('support_switch_bgp')
syslog.syslog(syslog.LOG_INFO, "Executing script")

from pattern import set_rule_pattern, set_portnumber, set_decision, mysql_save

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

# Script init
script_name = sys.argv[0]

pattern = sys.argv[1]
print(pattern)
set_rule_pattern(pattern)
# info = ("We received following pattern from RSyslog {0}").format(pattern)
# os.system('logger -t montag -p user.info ' + info)

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company, room_id = get_credentials()

# Log sample
# Jan 13 17:34:45 OS6900-ISP-Orange swlogd bgp_0 peer INFO: [peer(172.16.40.1),100] transitioned to IDLE state.

last = ""
with open("/var/log/devices/lastlog_bgp.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_bgp.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_bgp.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd= log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
        print(msg)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog IP Address: " + ipadd)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog Hostname: " + host)
        #syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + msg)
        bgp_peer, bgp_as, final_state = re.findall(r"peer INFO: \[peer\((.*?)\),(.*?)\] transitioned to (.*?) state.", msg)[0]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_bgp.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_bgp.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_bgp.json - Index error in regex")
        exit()

set_portnumber("0")
if alelog.rsyslog_script_timeout(ipadd+ "0" + pattern, time.time()):
    print("Less than 5 min")
    syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
    exit(0)

if "ESTABLISHED" in final_state:
    notif = "Preventive Maintenance Application - BGP Peering state change on OmniSwitch {0} / {1}\n\nDetails:\n- BGP Peer IP Address/AS : {2} / {3}\n- State : {4}".format(host, ipadd, bgp_peer, bgp_as, final_state)
    syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
    syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Send notification")
    send_message(notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
else:
    notif = "Preventive Maintenance Application - BGP Peering state change on OmniSwitch {0} / {1}\n\nDetails:\n- BGP Peer IP Address/AS : {2} / {3}\n- State : {4}\n\nPlease check the BGP Peer Node connectivity.".format(host, ipadd, bgp_peer, bgp_as, final_state)
    syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send notification")
    send_message(notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

set_decision(ipadd, "4")
try:
    mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
    syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision")    
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass   

