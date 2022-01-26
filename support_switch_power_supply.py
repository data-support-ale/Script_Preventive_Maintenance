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

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

switch_user, switch_password, jid, gmail_user, gmail_password, mails,ip_server_log = get_credentials()
ip_switch,nb_power_supply  = extract_ip_port("power_supply_down")



if jid !='':
         info = "Log of device : {0}".format(ip_switch)
         send_file(info,jid,ip_switch)
         info = "A default on Power supply {} from device {} has been detected".format(nb_power_supply,ip_switch)
         send_message(info,jid)

open('/var/log/devices/lastlog_power_supply_down.json','w').close()

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ip, "PS_Unit": nb_power_supply}, "fields": {"count": 1}}])
except UnboundLocalError as error:
    print(error)
    sys.exit()
