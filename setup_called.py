#!/usr/bin/env python3

import sys
import os
import re
import json
from support_tools_OmniSwitch import get_credentials
from time import strftime, localtime
from support_send_notification import send_message,send_file
import requests

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from ALE_script.conf
switch_user, switch_password, jid, gmail_user, gmail_password, mails, ip_server, company, mails_raw = get_credentials()
#company="Default"

## Notification sent to ALE admin for setting up VNA Workflow based on customer settings
subject = ("NBD Preventive Maintenance - There is a new Setup, End Customer: \"{0}\"").format(company)
body = "Attached to this message the configuration file, please setup the VNA accordingly"
url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Setup_File"
headers = {  'Content-type':"text/plain",'Content-Disposition': "attachment;filename=ALE_script.conf", 'jid1': '{0}'.format(jid),'toto': '{0}'.format(subject),'tata': '{0}'.format(body)}
files = {'file': open('/opt/ALE_Script/ALE_script.conf','r')}
response = requests.post(url,files=files, headers=headers)

if mails_raw != "":
    print(mails_raw)
    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_New_Bubble"
    headers = {'Content-type': 'application/json', "Accept-Charset": "UTF-8", 'mails': '{0}'.format(mails_raw),'company': '{0}'.format(company)}
    response = requests.get(url, headers=headers)
    response = str(response.content)
    response = response.replace("b", "", 1)
    response = response.replace("\'", "", 2)
    print(response)

    room = response
    mail = re.sub(r";", '"}, {"email": "', mails_raw)
    company = company
    name = "TECH_SUPPORT_NOTIF_" + company

    with open("/opt/ALE_Script/json/workflow_generic.json", "r") as fichier:
        json_result = str(fichier.read())
        json_result = re.sub(r"\$room", room, json_result)
        json_result = re.sub(r"\$email", mail, json_result)
        json_result = re.sub(r"\$company", company, json_result)
        json_result = re.sub(r"\$name", name, json_result)

            
    with open("/opt/ALE_Script/json/workflow_generic_result.json", "w") as fichier:
        fichier.write(json_result)



    with open("/opt/ALE_Script/json/workflow_generic_result.json", "r") as fichier:
        data = str(fichier.read())

    url = "https://tpe-vna.al-mydemo.com/management/api/users/me"

    payload={}
    headers = {
    'Authorization': 'Basic anRyZWJhb2w6anRyZWJhb2w=',
    'Cookie': 'JSESSIONID=80E64766B76B28CBFF0B44B3876ADA01'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    json_response = json.loads(response.text)
    tenant_id = json_response["tenantId"]

    url = "https://tpe-vna.al-mydemo.com/management/api/tenants/{}/flows/import/".format(tenant_id)

    payload = data
    headers = {
    'Origin': 'https://tpe-vna.al-mydemo.com',
    'Referer': 'https://tpe-vna.al-mydemo.com/app/editor',
    'X-Requested-With': 'XMLHttpRequest',
    'Authorization': 'Basic anRyZWJhb2w6anRyZWJhb2w=',
    'Content-Type': 'application/json',
    'Cookie': 'JSESSIONID=8B4E6097CB90CE188EB443B4D95EE13A'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    json_response = json.loads(response.text)
    id = json_response["id"]

    url = "https://tpe-vna.al-mydemo.com/management/api/tenants/{}/flows/{}/imported".format(tenant_id, id)

    payload = re.sub(r"%uuid_0%", id, payload)
    payload = re.sub(r"%tenantName%", "NBDNotif_Classic_"+company, payload,1)
    payload = re.sub(r"%tenantName%", "NBDNotif_File_"+company, payload,1)
    payload = re.sub(r"%tenantName%", "NBDNotif_Alert_"+company, payload,1)
    payload = re.sub(r"%tenantName%", "NBDNotif_Test_"+company, payload,1)
    headers = {
    'Authorization': 'Basic anRyZWJhb2w6anRyZWJhb2w=',
    'Content-Type': 'application/json',
    'Cookie': 'JSESSIONID=80E64766B76B28CBFF0B44B3876ADA01'
    }

    response = requests.request("PUT", url, headers=headers, data=payload)

    print(response)


    url = "https://tpe-vna.al-mydemo.com/management/api/tenants/{}/flows/{}/deploy".format(tenant_id, id)


    response = requests.request("PUT", url, headers=headers, data=payload)

    print(response)


if mails != "":
    print(mails)