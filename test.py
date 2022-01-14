#!/usr/bin/env python

import sys
import os
import re
import json
from support_tools import enable_debugging, disable_debugging, disable_port, extract_ip_port, check_timestamp, get_credentials,extract_ip_ddos,disable_debugging_ddos,enable_qos_ddos,get_id_client,get_server_log_ip
from time import strftime, localtime, sleep
from support_send_notification import send_message, send_mail,send_file
import requests

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user, switch_password, jid, gmail_user, gmail_password, mails, ip_server = get_credentials()

## If we put argument when calling the script we can test different Workflows (companies)
if sys.argv[1] != None:
    company = sys.argv[1]
    print(company)
    info = "NBD Preventive Maintenance - This is a test!"
    url = ("https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Classic_{0}").format(company)
    headers = {
              'Content-type': 'application/json', 
              "Accept-Charset": "UTF-8", 
              'jid1': '{0}'.format(jid), 
              'toto': '{0}'.format(info),
              'Card': '0'
              }
    response = requests.get(url, headers=headers)

    url = ("https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_File_{0}").format(company)
    payload=open("/opt/ALE_Script/giphy.gif", "rb")
    headers = {
              'jid1': '{0}'.format(jid),
              'toto': '{0}'.format(info),
              'Authorization': 'Basic anRyZWJhb2w6anRyZWJhb2w=',
              'Content-Type': 'image/gif',
              'Content-Disposition' : 'attachment; filename=welcome.gif'
              }
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)

else:
    print("Please provide Company name in argument when executing this script")