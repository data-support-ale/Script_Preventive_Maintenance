#!/usr/bin/env python3

import sys
import os
import re
import json
from support_tools import enable_debugging, disable_debugging, disable_port, extract_ip_port, check_timestamp, get_credentials,extract_ip_ddos,disable_debugging_ddos,enable_qos_ddos,get_id_client,get_server_log_ip
from time import strftime, localtime, sleep
from support_send_notification import send_message, send_mail,send_file


# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user, switch_password, jid, gmail_user, gmail_password, mails, ip_server = get_credentials()
ip_server_log = get_server_log_ip()

last = ""
with open("/var/log/devices/lastlog_authfail.json", "r") as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_authfail.json","w") as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_authfail.json", "r") as log_file:
    log_json = json.load(log_file)
    ip = log_json["relayip"]
    nom = log_json["hostname"]
    msg = log_json["message"]

    user = re.findall(r"user (.*)", msg)[0]

if jid != '':
    notif = "Authentication failed on " + ip + " user " + user
    send_message(notif, jid)
else:
    print("Mail request set as no")
    os.system('logger -t montag -p user.info Mail request set as no')
    sleep(1)
    open('/var/log/devices/lastlog_auth_fail.json', 'w').close()

