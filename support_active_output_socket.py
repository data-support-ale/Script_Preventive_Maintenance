#!/usr/bin/env python

import sys
import os
import getopt
import json
import logging
import subprocess
from support_tools import extract_ip_ov,get_credentials
from time import gmtime, strftime, localtime, sleep
import re #Regex

#Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
switch_user, switch_password, jid, gmail_user, gmail_password, mails, ip_server_log = get_credentials()

extract_ip_ov()
content_variable = open ('/opt/ALE_Script/device_catalog.conf','r')
file_lines = content_variable.readlines()
content_variable.close()


ips_address = file_lines[0].split(',')
for ip_address in ips_address:
   cmd = "swlog output socket {0}".format(ip_server_log)
   #ssh session to start python script remotely
   os.system('logger -t montag -p user.info swlog output socket activation')
   os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user, ip_address, cmd)) 
   print(ip_address)
