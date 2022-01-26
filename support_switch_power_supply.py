#!/usr/bin/env python

import sys
import os
import getopt
import json
import logging
import datetime
from time import strftime, localtime
from support_tools_OmniSwitch import get_credentials
from support_send_notification import send_message,send_file
import subprocess
from database_conf import *
import re

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

switch_user,switch_password,mails,jid,ip_server,login_AP,pass_AP,tech_pass,random_id,company = get_credentials()

last = ""
with open("/var/log/devices/lastlog_power_supply_down.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_power_supply_down.json","w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_power_supply_down.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ip_switch = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_power_supply_down.json empty")
        exit()

    nb_power_supply = re.findall(r"Supply (.*?)", msg)[0]

if jid !='':
         info = "Log of device : {0}".format(ip_switch)
         send_file(info,jid,ip_switch)
         info = "A default on Power supply {} from device {} has been detected".format(nb_power_supply,ip_switch)
         send_message(info,jid)

open('/var/log/devices/lastlog_power_supply_down.json','w').close()

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ip_switch, "PS_Unit": nb_power_supply}, "fields": {"count": 1}}])
except UnboundLocalError as error:
    print(error)
    sys.exit()
