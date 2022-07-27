#!/usr/local/bin/python3.7

import sys
import os
import re
import json
from support_tools_OmniSwitch import get_credentials
from time import strftime, localtime, sleep
from support_send_notification import send_message_detailed
from database_conf import *
import syslog

syslog.openlog('support_switch_ospf')
syslog.syslog(syslog.LOG_INFO, "Executing script")


runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]

switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

# Log sample
# OS6860E_VC_Core swlogd ospf_nbr.c ospfNbrStateMachine 0 ospf_0 STATE EVENT: CUSTLOG CMM OSPF neighbor state change for 172.25.136.2, router-id 172.25.136.2: FULL to DOWN

last = ""
with open("/var/log/devices/lastlog_ospf.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_ospf.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_ospf.json", "r", errors='ignore') as log_file:
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
        print("File /var/log/devices/lastlog_ospf.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_ospf.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_ospf.json - Index error in regex")
        exit()

    try:    
        neighbor_ip, router_id, initial_state, final_state = re.findall(r"CUSTLOG CMM OSPF neighbor state change for (.*?), router-id (.*?): (.*?) to (.*)", msg)[0]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_ospf.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_ospf.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_ospf.json - Index error in regex")
        exit()

if "FULL" in final_state:
    syslog.syslog(syslog.LOG_DEBUG, "Final State is FULL")
    notif = ("Preventive Maintenance Application - OSPF Neighbor state change on OmniSwitch {0} / {1}.\n\nDetails:\n- Router-ID: {2}\n- Neighbor-ID {3}\n- Initial State: {4}\n- Final State: {5}.").format(host,ipadd,router_id,neighbor_ip,initial_state,final_state)
    syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
    send_message_detailed(notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
else:
    notif = ("Preventive Maintenance Application - OSPF Neighbor state change on OmniSwitch {0} / {1}.\n\nDetails:\n- Router-ID: {2}\n- Neighbor-ID {3}\n- Initial State: {4}\n- Final State: {5}\nPlease check the OSPF Neighbor node connectivity.").format(host,ipadd,router_id,neighbor_ip,initial_state,final_state)
    syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
    send_message_detailed(notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"OSPF_Neighbor_IP": neighbor_ip, "IP": ipadd, "OSPF_Router_ID": router_id, "State": final_state}, "fields": {"count": 1}}])
    syslog.syslog(syslog.LOG_INFO, "Statistics saved")
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass 
