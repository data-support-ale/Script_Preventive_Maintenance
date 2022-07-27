#!/usr/bin/env python3

import sys
import os
import re
import json
from support_tools_OmniSwitch import get_credentials
from time import strftime, localtime, sleep
from support_send_notification import *
# from database_conf import *
import time

from pattern import set_rule_pattern, set_portnumber, set_decision, mysql_save

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)

pattern = sys.argv[1]
print(pattern)
set_rule_pattern(pattern)
# info = ("We received following pattern from RSyslog {0}").format(pattern)
# os.system('logger -t montag -p user.info ' + info)

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company, room_id = get_credentials()

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
        ip = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
        bgp_peer, bgp_as, final_state = re.findall(
            r"peer INFO: \[peer\((.*?)\),(.*?)\] transitioned to (.*?) state.", msg)[0]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_bgp.json empty")
        exit()
    except IndexError:
        print("Index error in regex")
        exit()

set_portnumber("0")
if alelog.rsyslog_script_timeout(ip + "0" + pattern, time.time()):
    print("Less than 5 min")
    exit(0)

if jid1 != '' or jid2 != '' or jid3 != '':
    #notif = "BGP Peering state change on OmniSwitch \"" + host + "\" IP: " + ip + " BGP Peer IP Address/AS " + bgp_peer + "/" + bgp_as + " to " + final_state
    if "ESTABLISHED" in final_state:
        notif = "Preventive Maintenance Application - BGP Peering state change on OmniSwitch {0} / {1}\n\nDetails:\n- BGP Peer IP Address/AS : {2} / {3}\n- State : {4}".format(host, ip, bgp_peer, bgp_as, final_state)
        send_message_detailed(notif, jid1, jid2, jid3)
        set_decision(ip, "4")
        mysql_save(runtime=_runtime, ip_address=ip, result='success', reason=notif, exception='')
        sys.exit(0)
    else:
        notif = "Preventive Maintenance Application - BGP Peering state change on OmniSwitch {0} / {1}\n\nDetails:\n- BGP Peer IP Address/AS : {2} / {3}\n- State : {4}\n\nPlease check the BGP Peer Node connectivity.".format(host, ip, bgp_peer, bgp_as, final_state)
        send_message_detailed(notif, jid1, jid2, jid3)
        set_decision(ip, "4")
        mysql_save(runtime=_runtime, ip_address=ip, result='success', reason=notif, exception='')
        sys.exit(0)
else:
    print("Mail request set as no")
    set_decision(ip, "4")
    mysql_save(runtime=_runtime, ip_address=ip, result='success', reason="Mail request set as no", exception='')
    
    os.system('logger -t montag -p user.info Mail request set as no')
    sleep(1)
    open('/var/log/devices/lastlog_bgp.json', 'w', errors='ignore').close()
