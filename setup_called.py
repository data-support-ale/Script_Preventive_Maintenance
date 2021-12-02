#!/usr/bin/env python3

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

# Get informations from ALE_script.conf
switch_user, switch_password, jid, gmail_user, gmail_password, mails, ip_server = get_credentials()
company="Default"

## Notification sent to ALE admin for setting up VNA Workflow based on customer settings
if sys.argv[1] != "Default":
    company = sys.argv[1]
    print(company)
    subject = ("NBD Preventive Maintenance - There is a new Setup, End Customer: \"{0}\"").format(company)
    body = "Attached to this message the configuration file, please setup the VNA accordingly"
    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Setup_File"
    headers = {  'Content-type':"text/plain",'Content-Disposition': "attachment;filename=ALE_script.conf", 'jid1': '{0}'.format(jid),'toto': '{0}'.format(subject),'tata': '{0}'.format(body)}
    files = {'file': open('/opt/ALE_Script/ALE_script.conf','r')}
    response = requests.post(url,files=files, headers=headers)
else:
    sys.exit(2)