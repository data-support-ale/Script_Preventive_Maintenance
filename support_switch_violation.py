#!/usr/bin/env python

import sys
import os
import re
import json
from support_tools import enable_debugging, disable_debugging, disable_port, extract_ip_port, check_timestamp, \
    get_credentials, extract_ip_ddos, disable_debugging_ddos, enable_qos_ddos, get_id_client, get_server_log_ip, \
    get_jid, format_mac
from time import strftime, localtime, sleep
from support_send_notification import send_message, send_mail, send_file
from support_response_handler import request_handler_mail, request_handler_rainbow, request_handler_both
from database_conf import *

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user, switch_password, jid, gmail_user, gmail_password, mails, ip_server = get_credentials()

last = ""
with open("/var/log/devices/lastlog_violation.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_violation.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_violation.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ip = log_json["relayip"]
        nom = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_violation.json empty")
        exit()

    port, reason = re.findall(r"Port (.*?) in violation - source (.*?) reason", msg)[0]

    if reason == "0":
        reason = "Unknown"
    elif reason == "1":
        reason = "Access Guardian"
    elif reason == "2":
        reason = "QOS Policy"
    elif reason == "3":
        reason = "Net Sec"
    elif reason == "4":
        reason = "UDLD"
    elif reason == "5":
        reason = "NI supervision (Fabric Stability)"
    elif reason == "6":
        reason = "OAM"
    elif reason == "8":
        reason = "LFP"
    elif reason == "9":
        reason = "Link monitoring"
    elif reason == "10":
        reason = "LBD"
    elif reason == "11":
        reason = "SPB"
    elif reason == "12":
        reason = "ESM"
    elif reason == "13":
        reason = "ESM"
    elif reason == "14":
        reason = "LLDP"

print(gmail_user)

if gmail_user != '' and jid != '':
    notif = "A port violation occurs on OmniSwitch " + nom + "port " + port + ", source: " + reason + ". Do you want to clear the violation?"
    answer = request_handler_both(ip,'0',port,'0',notif,get_jid(),get_server_log_ip(),get_id_client(),"duplicate") #new method

elif gmail_user != '':
    notif = "A port violation occurs on OmniSwitch " + nom + "port " + port + ", source: " + reason + ". Do you want to clear the violation?"
    answer = request_handler_mail(ip,'0',port,'0',notif,get_jid(),get_server_log_ip(),get_id_client(),"duplicate") #new method

elif jid != '':
    notif = "A port violation occurs on OmniSwitch " + nom + "port " + port + ", source: " + reason + ". Do you want to clear the violation?"
    answer = request_handler_rainbow(ip,'0',port,'0',notif,get_jid(),get_server_log_ip(),get_id_client(),"duplicate") #new method
else:
    answer = '1'

if answer == '1':
    os.system('logger -t montag -p user.info Process terminated')
    # CLEAR VIOLATION
    cmd = "clear violation port " + port
    os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user, ip,cmd))
    if jid != '':
        info = "Log of device : {0}".format(ip)
        send_file(info, jid, ip)
        info = "A port violation has been cleared up on device {}".format(ip)
        send_message(info, jid)

else:
    print("Mail request set as no")
    os.system('logger -t montag -p user.info Mail request set as no')
    sleep(1)

from database_conf import *
write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ip, "Reason": reason, "port" : port}, "fields": {"count": 1}}])
