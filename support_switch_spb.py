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
#{"@timestamp":"2022-01-11T14:30:23+01:00","type":"syslog_json","relayip":"10.130.7.245","hostname":"os6900_vc_core","message":"<134>Jan 11 14:30:23 OS6900_VC_Core swlogd isis_spb_0 ADJACENCY INFO: Lost L1 adjacency with e8e7.32f5.b58b on ifId 1013","end_msg":""}

last = ""
with open("/var/log/devices/lastlog_spb.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_spb.json","w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_spb.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ip = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_spb.json empty")
        exit()

    adjacency_id,port_1 = re.findall(r"Lost L1 adjacency with (.*?) on ifId (.*)", msg)[0]
    #n=int(port_1)
    n = len(str(port_1))
    print(n)
    dig = []
    dig = list(int(port_1) for port_1 in str(port_1))
    if n < 6:
        dig_1 = [1, 0]
        dig = dig_1 + dig
    unit = dig[0]
    slot = dig[2]
    port = str(dig[4]) + str(dig[5])
    if n > 6:
        port = str(dig[7])
    port = str(unit) + "/" + str(slot) + "/" + str(port)
    print(port)

if jid != '':
    notif = "SPB Adjacency state change on OmniSwitch \"" + host + "\" IP: " + ip + " System ID " + adjacency_id + " from port " + port
    send_message(notif, jid)
else:
    print("Mail request set as no")
    os.system('logger -t montag -p user.info Mail request set as no')
    sleep(1)
    open('/var/log/devices/lastlog_spb.json', 'w').close()

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"System_ID": adjacency_id, "IP": ip, "Port" : port}, "fields": {"count": 1}}])
except UnboundLocalError as error:
    print(error)
    sys.exit()

