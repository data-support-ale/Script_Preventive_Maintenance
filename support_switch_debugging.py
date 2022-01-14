#!/usr/bin/env python

import sys
import os
import getopt
import json
import logging
import subprocess
from support_tools import enable_debugging, disable_debugging, disable_port, extract_ip_port, check_timestamp, get_credentials
from time import gmtime, strftime, localtime, sleep
from support_send_notification import  send_message
#Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

#Get informations from logs.
switch_user, switch_password, jid, gmail_usr, gmail_passwd, mails,ip_server = get_credentials()
ip_switch, portnumber = extract_ip_port("debug")




print("call function enable debugging")
enable_debugging(switch_user,switch_password,ip_switch)
os.system('logger -t montag -p user.info Process terminated')

# clear lastlog file
open('/var/log/devices/lastlog.json','w').close()

sys.exit(0)

