#!/usr/bin/env python

import sys
import os
import re
import json
from support_tools import enable_debugging, disable_debugging, disable_port, extract_ip_port, check_timestamp, get_credentials,extract_ip_ddos,disable_debugging_ddos,enable_qos_ddos,get_id_client,get_server_log_ip, get_jid, format_mac
from time import strftime, localtime, sleep
from support_send_notification import send_message, send_mail,send_file
from support_response_handler import request_handler_mail,request_handler_rainbow,request_handler_both


# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user, switch_password, jid, gmail_user, gmail_password, mails, ip_server = get_credentials()

last = ""
with open("/var/log/devices/lastlog_dupip.json", "r") as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_dupip.json", "w") as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_dupip.json", "r") as log_file:
    log_json = json.load(log_file)
    ip = log_json["relayip"]
    nom = log_json["hostname"]
    msg = log_json["message"]

    ip_dup, port, mac = re.findall(r"duplicate IP address (.*?) from port (.*?) eth addr (.*)", msg)[0]
    mac = format_mac(mac)

if gmail_user != '' and jid != '':
    notif = "IP address duplication (" + ip_dup + ") on port " + port + " of switch " + ip + "(" + nom + "). Do you want to blacklist mac : " + mac + " ?"
    answer = request_handler_both(ip,'0',port,'0',notif,get_jid(),get_server_log_ip(),get_id_client(),"duplicate") #new method

elif gmail_user != '':
    notif = "IP address duplication (" + ip_dup + ") on port " + port + " of switch " + ip + "(" + nom + "). Do you want to blacklist mac : " + mac + " ?"
    answer = request_handler_mail(ip,'0',port,'0',notif,get_jid(),get_server_log_ip(),get_id_client(),"duplicate") #new method

elif jid != '':
    notif = "IP address duplication (" + ip_dup + ") on port " + port + " of switch " + ip + "(" + nom + "). Do you want to blacklist mac : " + mac + " ?"
    answer = request_handler_rainbow(ip,'0',port,'0',notif,get_jid(),get_server_log_ip(),get_id_client(),"duplicate") #new method
else:
    answer = '1'

if answer == '1':
    os.system('logger -t montag -p user.info Process terminated')
    enable_qos_ddos(switch_user,switch_password,ip,mac)
    if jid != '':
        info = "Log of device : {0}".format(ip)
        send_file(info, jid, ip)
        info = "A IP duplication has been detected on your network and QOS policy has been applied to prevent access for the MAC Address {0} to device {1}".format(mac, ip)
        send_message(info, jid)
else:
    print("Mail request set as no")
    os.system('logger -t montag -p user.info Mail request set as no')
    sleep(1)


from database_conf import *
write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ip, "IP_dup": ip_dup, "mac" : mac}, "fields": {"count": 1}}])
