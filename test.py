#!/usr/bin/env python

import sys
import os
from support_tools_OmniSwitch import get_credentials
from time import strftime, localtime
import requests
from database_conf import *

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

# If we put argument when calling the script we can test different Workflows (companies)
if sys.argv[1] != None:
    company = sys.argv[1]
    print(company)
    info = "NBD Preventive Maintenance - This is a test!"
    url = (
        "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Classic_{0}").format(company)
    headers = {
        'Content-type': 'application/json',
        "Accept-Charset": "UTF-8",
        'jid1': '{0}'.format(jid),
        'toto': '{0}'.format(info),
        'Card': '0'
    }
    response = requests.get(url, headers=headers)
    print(response)
    try:
        write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                        "HTTP_Request": url, "HTTP_Response": response}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()

    url = (
        "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_File_{0}").format(company)
    payload = open("/opt/ALE_Script/VNA_Workflow/images/giphy.gif", "rb")
    headers = {
        'jid1': '{0}'.format(jid),
        'toto': '{0}'.format(info),
        'Authorization': 'Basic anRyZWJhb2w6anRyZWJhb2w=',
        'Content-Type': 'image/gif',
        'Content-Disposition': 'attachment; filename=welcome.gif'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response)
    try:
        write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                        "HTTP_Request": url, "HTTP_Response": response}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()

else:
    print("Please provide Company name in argument when executing this script")
