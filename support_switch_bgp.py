#!/usr/bin/env python

import sys
import os
import re
import json
from support_tools_OmniSwitch import get_credentials
from time import strftime, localtime, sleep
from support_send_notification import send_message
from database_conf import *

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user,switch_password,jid,gmail_usr,gmail_passwd,mails,ip_server_log,company,mails_raw = get_credentials()

# Log sample
#Jan 13 17:34:45 OS6900-ISP-Orange swlogd bgp_0 peer INFO: [peer(172.16.40.1),100] transitioned to IDLE state.

last = ""
with open("/var/log/devices/lastlog_bgp.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_bgp.json","w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_bgp.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ip = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_bgp.json empty")
        exit()

    bgp_peer,bgp_as,final_state = re.findall(r"peer INFO: \[peer\((.*?)\),(.*?)\] transitioned to (.*?) state.", msg)[0]

if jid != '':
    notif = "BGP Peering state change on OmniSwitch \"" + host + "\" IP: " + ip + " BGP Peer IP Address/AS " + bgp_peer + "/" + bgp_as + " to " + final_state
    send_message(notif, jid)
else:
    print("Mail request set as no")
    os.system('logger -t montag -p user.info Mail request set as no')
    sleep(1)
    open('/var/log/devices/lastlog_bgp.json', 'w', errors='ignore').close()

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"BGP_Peer_IP": bgp_peer, "IP": ip, "BGP_AS" : bgp_as, "State" : final_state}, "fields": {"count": 1}}])
except UnboundLocalError as error:
    print(error)
    sys.exit()
