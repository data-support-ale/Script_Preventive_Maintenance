#!/usr/local/bin/python3.7

import sys
import os
import re
import json
from support_tools_OmniSwitch import get_credentials
from time import strftime, localtime
import requests

# Aim of this script: notify ALE Admin that Preventive Maintenance setup is called and provides customer environment data. Automate the VNA Worklow deployment and Rainbow Bubble

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

path = "/opt/ALE_Script"

# Get informations from ALE_script.conf (mails, mails_raw, company name)

switch_user, switch_password, mails, jid1, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

if(get_credentials("room_id") != ""):
    sys.exit()

# Notification sent to ALE admin for notifying ALE Admin on a dedicated Rainbow bubble that a setup init is called
subject = (
    "NBD Preventive Maintenance - There is a new Setup, End Customer: \"{0}\"").format(company)
body = "Attached to this message the configuration file, please setup the VNA accordingly"
url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Setup_File"
headers = {	
    'Content-type': "text/plain", 	
    'Content-Disposition': "attachment;filename=ALE_script.conf",	
    'jid1': '{0}'.format(jid1), 	
    'toto': '{0}'.format(subject), 	
    'tata': '{0}'.format(body)	
}
# ALE_Script.conf is attached in the ALE Admin Rainbow bubble
files = {'file': open(path + '/ALE_script.conf', 'r')}
response = requests.post(url, files=files, headers=headers)
# mails_raw format: email_1;email_2;email_3
try:
    if mails != "":
        print(mails)
        url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_New_Bubble"
        headers = {'Content-type': 'application/json', "Accept-Charset": "UTF-8",
                   'mails': '{0}'.format(mails), 'company': '{0}'.format(company)}
        response = requests.get(url, headers=headers)
        response = str(response.content)
        response = response.replace("b", "", 1)
        response = response.replace("\'", "", 2)
        print(response)
        room = response
        mail = re.sub(r";", '"}, {"email": "', mails)
        company = company
        name = "TECH_SUPPORT_NOTIF_" + company

        with open(path + "/ALE_script.conf", "r", errors='ignore') as ALE_conf:
            data_conf = ALE_conf.read()
        with open(path + "/ALE_script.conf", "w+", errors='ignore') as ALE_conf:
            ALE_conf.write((str(data_conf)+str(room).strip()
                            ).replace("\n", "").replace(" ", "") + ",\n")

    # All generic fields (Rainbow bubble, emails, workflow name) are replaced based on ALE_script.conf file and Room_ID received from api/flows/NBDNotif_New_Bubble
        with open(path + "/VNA_Workflow/json/workflow_generic.json", "r", errors='ignore') as file_json:
            json_result = str(file_json.read())
            json_result = re.sub(r"\$room", room, json_result)
            json_result = re.sub(r"\$email", mail, json_result)
            json_result = re.sub(r"\$company", company, json_result)
            json_result = re.sub(r"\$name", name, json_result)
        with open(path + "/VNA_Workflow/json/workflow_generic_result.json", "w", errors='ignore') as file_json:
            file_json.write(json_result)
        with open(path + "/VNA_Workflow/json/workflow_generic_result.json", "r", errors='ignore') as file_json:
            data = str(file_json.read())

    # REST-API method GET for Login to VNA
        url = "https://tpe-vna.al-mydemo.com/management/api/users/me"
        # example : {"id":"4bf9fa8b-ad91-4f3b-ba55-d98183dc5c02","created":1638355705248,"updated":null,"loginName":"jtrebaol","fullName":"Jonathan TREBAOL","email":"jonathan.trebaol@al-enterprise.com","roles":["DirectoryManagement","EditorManagement","UserManagement","StatisticsManagement","GroupsManagement","SiteManagement","TenantAdminManagement","PromptManagement"],"active":true,"tenantId":"15c2a6b5-ef66-4424-99a9-227e7643f96d"}
        payload = {}
        headers = {
            # Basic Auth code from credentials (reference https://www.blitter.se/utils/basic-authentication-header-generator/)
            'Authorization': 'Basic anRyZWJhb2w6anRyZWJhb2w=',
            # Cookie of the session (value dont matter)
            'Cookie': 'JSESSIONID=80E64766B76B28CBFF0B44B3876ADA01'
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        json_response = json.loads(response.text)
        tenant_id = json_response["tenantId"]

    # REST-API method POST /api/tenants/<tenant_id>/flows/import is called within payload the workflow_generic_result.json file. <tenant_id> value is received into the HTTP Get Answer when calling REST-API api/users/me
        url = "https://tpe-vna.al-mydemo.com/management/api/tenants/{}/flows/import/".format(
            tenant_id)  # This URL contains the tenant_id and enable the import
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
        payload = response.text

    # REST-API method PUT api/tenants/<tenant_id>/flows/<id>/imported is called within path <id> value received from REST-API /api/tenants/<tenant_id>/flows/import for validating  the VNA Workflow import
        url = "https://tpe-vna.al-mydemo.com/management/api/tenants/{}/flows/{}/imported".format(
            tenant_id, id)  # This URL validate the import use the tenant_id but also the import_id from the import request
        # replacement of different fields to specify the IDs in the .json before sending it out
        headers = {
            'Authorization': 'Basic anRyZWJhb2w6anRyZWJhb2w=',
            'Content-Type': 'application/json',
            'Cookie': 'JSESSIONID=80E64766B76B28CBFF0B44B3876ADA01'
        }

        payload = re.sub(r"\$tenantName1", "NBDNotif_Classic_"+company, payload, 1)
        payload = re.sub(r"\$tenantName2", "NBDNotif_File_"+company, payload, 1)
        payload = re.sub(r"\$tenantName3", "NBDNotif_Alert_" +company, payload, 1)
        payload = re.sub(r"\$tenantName4", "NBDNotif_Test_"+company, payload, 1)

        response = requests.request("PUT", url, headers=headers, data=payload)
        if response.status_code == 200:
            os.system('logger -t montag -p user.info 200 OK')
            print("VNA Workflow registering in progress")
        elif response.status_code == 400:
            os.system('logger -t montag -p user.info 400 OK')
            print("VNA Workflow already register")
        else:
            os.system('logger -t montag -p user.info REST API Call Failure')
            print("VNA Workflow registering failed")

    # REST-API method PUT /api/tenants/<tenant_id>/flows/<id>/deploy is called for enabling the VNA Workflow
        url = "https://tpe-vna.al-mydemo.com/management/api/tenants/{}/flows/{}/deploy".format(
            tenant_id, id)
        response = requests.request("PUT", url, headers=headers, data=payload)
        if response.status_code == 200:
            os.system('logger -t montag -p user.info 200 OK')
            print("VNA Workflow deployed and enabled")
        elif response.status_code == 400:
            os.system('logger -t montag -p user.info 400 OK')
            print("VNA Workflow already deployed")
            sys.exit()
        else:
            os.system('logger -t montag -p user.info REST API Call Failure')
            print("VNA Workflow depoyment failed")

    # REST-API for sending Welcome gif to Rainbow bubble
        url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_File_{0}".format(company)
        payload = open(path + "/VNA_Workflow/images/giphy.gif", "rb")
        headers = {	
            'Authorization': 'Basic anRyZWJhb2w6anRyZWJhb2w=',	
            'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",	
            'Content-Type': 'image/gif',	
            'jid1': '{0}'.format(jid1), 	
            'subject': '{0}'.format('sending Welcome gif to Rainbow bubble'),	
            'action': '{0}'.format('Welcome to the Club'),	
            'result': '{0}'.format('Status: Success'),	
            'Email': '0'	
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            os.system('logger -t montag -p user.info 200 OK')
            print("Rainbow bubble created")
        elif response.status_code == 400:
            os.system('logger -t montag -p user.info 400 OK')
            print("Rainbow bubble aldready created")
        else:
            os.system('logger -t montag -p user.info REST API Call Failure')
            print("Rainbow bubble creation failed")

    else:
        print("There are no emails saved into the database")
        sys.exit()
except ValueError:
    print("There are no emails saved into the database")
    sys.exit()
except EOFError:
    print("There are no emails saved into the database")
    sys.exit()
except KeyboardInterrupt:
    print("User hits the interrupt key. Function set_called aborted")
    sys.exit()
