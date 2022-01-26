#!/usr/bin/env python

import sys
import os
import json
import re
from support_tools_OmniSwitch import get_credentials, debugging
from time import gmtime, strftime, localtime, sleep
from support_send_notification import  send_message
from database_conf import *

#Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

#Get informations from logs.
switch_user,switch_password,mails,jid,ip_server,login_AP,pass_AP,tech_pass,random_id,company = get_credentials()

last = ""
with open("/var/log/devices/lastlog_ddos.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_ddos.json","w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_ddos.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ip = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_ddos.json empty")
        exit()

    ddos_type = re.findall(r"Denial of Service attack detected: <(.*?)>", msg)[0]

if jid != '':
    notif = "A Denial of Service Attack is detected on OmniSwitch \"" + host + "\" IP: " + ip + " of type " + ddos_type
    send_message(notif, jid)
    try:
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ip, "DDOS_Type": ddos_type}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()

# Enable debugging logs for getting IP Attacker's IP Address "swlog appid ipv4 subapp all level debug3"
appid = "ipv4"
subapp = "all"
level = "debug3"
# Call debugging function from support_tools_OmniSwitch
debugging(ip,appid,subapp,level)

os.system('logger -t montag -p user.info Process terminated')
# clear lastlog file
open('/var/log/devices/lastlog_ddos.json','w').close()

sys.exit(0)

