#!/usr/local/bin/python3.7

import sys
import os
import re
import json
from support_tools_OmniSwitch import get_credentials
from time import strftime, localtime, sleep
from support_send_notification import send_message
from database_conf import *
import syslog

syslog.openlog('support_switch_bgp')
syslog.syslog(syslog.LOG_INFO, "Executing script")


runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

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
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
        print(msg)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog IP Address: " + ipadd)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog Hostname: " + host)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + msg)
        bgp_peer, bgp_as, final_state = re.findall(r"peer INFO: \[peer\((.*?)\),(.*?)\] transitioned to (.*?) state.", msg)[0]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_bgp.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_bgp.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_bgp.json - Index error in regex")
        exit()

if "ESTABLISHED" in final_state:
    notif = "Preventive Maintenance Application - BGP Peering state change on OmniSwitch {0} / {1}\n\nDetails:\n- BGP Peer IP Address/AS : {2} / {3}\n- State : {4}".format(host, ipadd, bgp_peer, bgp_as, final_state)
    syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
    syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Send notification")
    send_message(notif, jid)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
else:
    notif = "Preventive Maintenance Application - BGP Peering state change on OmniSwitch {0} / {1}\n\nDetails:\n- BGP Peer IP Address/AS : {2} / {3}\n- State : {4}\n\nPlease check the BGP Peer Node connectivity.".format(host, ipadd, bgp_peer, bgp_as, final_state)
    syslog.syslog(syslog.LOG_INFO, "Notificattion: " + notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send notification")
    send_message(notif, jid)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

open('/var/log/devices/lastlog_bgp.json', 'w', errors='ignore').close()

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"BGP_Peer_IP": bgp_peer, "IP": ipadd, "BGP_AS": bgp_as, "State": final_state}, "fields": {"count": 1}}])
    syslog.syslog(syslog.LOG_INFO, "Statistics saved")
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass
