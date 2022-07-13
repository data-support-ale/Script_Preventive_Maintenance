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
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

set_portnumber("1/1/36")
print("test1")
ipadd = "10.130.7.36"
notif = "Preventive Maintenance Application - Test1 coke and stock"
send_message_detailed(notif, jid1, jid2, jid3)
set_decision(ipadd, "1")
mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
sys.exit(0)