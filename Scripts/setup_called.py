#!/usr/local/bin/python3.7

import sys
import os
import re
import json
from support_tools_OmniSwitch import get_credentials
from time import strftime, localtime
import requests
import syslog

syslog.openlog('support_setup_called')
syslog.syslog(syslog.LOG_INFO, "Executing script")


runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]

path = "/opt/ALE_Script"
vna_url = "https://vna.preprod.omniaccess-stellar-asset-tracking.com/"
# Get informations from ALE_script.conf (mails, mails_raw, company name)

switch_user, switch_password, mails, jid1, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

# Aim of this script: notify ALE Admin that Preventive Maintenance setup is called and provides customer environment data. Automate the VNA Worklow deployment and Rainbow Bubble


if(get_credentials("room_id") != ""):
    syslog.syslog(syslog.LOG_INFO, "Room_ID already exists in the Configuration File - Script exit")
    sys.exit()

# Notification sent to ALE admin for notifying setup is called
syslog.syslog(syslog.LOG_INFO, "Notification sent to ALE admin for notifying setup is called")
subject = ("NBD Preventive Maintenance - There is a new Setup, End Customer: \"{0}\"").format(company)
body = "Attached to this message the configuration file, please setup the VNA accordingly"
url = vna_url + "/api/flows/NBDNotif_Setup_File"
headers = {	
    'Content-type': "text/plain", 	
    'Content-Disposition': "attachment;filename=ALE_script.conf",
    'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",	
    'jid1': '{0}'.format(jid1), 	
    'toto': '{0}'.format(subject), 	
    'tata': '{0}'.format(body)	
}
syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
syslog.syslog(syslog.LOG_INFO, "Body: " + body)
syslog.syslog(syslog.LOG_INFO, "URL: " + url)
headers_str = str(headers)
syslog.syslog(syslog.LOG_INFO, "Headers: " + headers_str)

# ALE_Script.conf is attached in the ALE Admin Rainbow bubble
files = {'file': open(path + '/ALE_script.conf', 'r')}
files_str = str(files)
syslog.syslog(syslog.LOG_INFO, "Configuration file content: " + files_str)
syslog.syslog(syslog.LOG_INFO, "Configuration file collected - Calling VNA API - Send File")
response = requests.post(url, files=files, headers=headers)
response_str = str(response)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent - VNA Answer: " + response_str)

# mails_raw format: email_1;email_2;email_3
try:
    if mails != "":
        print(mails)
        syslog.syslog(syslog.LOG_INFO, "User emails: " + mails)
        url = vna_url + "/api/flows/NBDNotif_New_Bubble"
        headers = {
            'Content-type': 'application/json', 
            'Accept-Charset': 'UTF-8',
            'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
            'mails': '{0}'.format(mails), 
            'company': '{0}'.format(company)}

        syslog.syslog(syslog.LOG_INFO, "URL: " + url)
        headers_str = str(headers)
        syslog.syslog(syslog.LOG_INFO, "Headers: " + headers_str)
        syslog.syslog(syslog.LOG_INFO, "Configuration file collected - Calling VNA API - /api/flows/NBDNotif_New_Bubble")
        response = requests.get(url, headers=headers)
        response_str = str(response)
        syslog.syslog(syslog.LOG_INFO, "Notification sent - VNA Answer: " + response_str)
        response = str(response.content)
        response = response.replace("b", "", 1)
        response = response.replace("\'", "", 2)
        print(response)
        room = response
        syslog.syslog(syslog.LOG_INFO, "Room_ID: " + room)
        mail = re.sub(r";", '"}, {"email": "', mails)
        company = company
        name = "TECH_SUPPORT_NOTIF_" + company

        with open(path + "/ALE_script.conf", "r", errors='ignore') as ALE_conf:
            data_conf = ALE_conf.read()
        with open(path + "/ALE_script.conf", "w+", errors='ignore') as ALE_conf:
            ALE_conf.write((str(data_conf)+str(room).strip()
                            ).replace("\n", "").replace(" ", "") + ",\n")

    # All generic fields (Rainbow bubble, emails, workflow name) are replaced based on ALE_script.conf file and Room_ID received from api/flows/NBDNotif_New_Bubble
        syslog.syslog(syslog.LOG_INFO, "Generating the workflow_generic.json file")
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
        #syslog.syslog(syslog.LOG_DEBUG, json_result)

    # REST-API method GET for Login to VNA
        syslog.syslog(syslog.LOG_INFO, "API for login to VNA")
        url = vna_url + "/management/api/users/me"
        # example : {"id":"4bf9fa8b-ad91-4f3b-ba55-d98183dc5c02","created":1638355705248,"updated":null,"loginName":"jtrebaol","fullName":"Jonathan TREBAOL","email":"jonathan.trebaol@al-enterprise.com","roles":["DirectoryManagement","EditorManagement","UserManagement","StatisticsManagement","GroupsManagement","SiteManagement","TenantAdminManagement","PromptManagement"],"active":true,"tenantId":"15c2a6b5-ef66-4424-99a9-227e7643f96d"}
        payload = {}
        headers = {
            # Basic Auth code from credentials (reference https://www.blitter.se/utils/basic-authentication-header-generator/)
            'Authorization': 'Basic anRyZWJhb2w6anRyZWJhb2w=',
            # Cookie of the session (value dont matter)
            'Cookie': 'JSESSIONID=80E64766B76B28CBFF0B44B3876ADA01'
        }
        syslog.syslog(syslog.LOG_INFO, "URL: " + url)
        headers_str = str(headers)
        syslog.syslog(syslog.LOG_INFO, "Headers: " + headers_str)

        syslog.syslog(syslog.LOG_INFO, "Configuration file collected - Calling VNA API - /management/api/users/me")
        response = requests.request("GET", url, headers=headers, data=payload)
        response_str = str(response)
        syslog.syslog(syslog.LOG_INFO, "Notification sent - VNA Answer: " + response_str)
        json_response = json.loads(response.text)
        tenant_id = json_response["tenantId"]
        syslog.syslog(syslog.LOG_INFO, "Notification sent - VNA Answer: " + str(json_response))
        syslog.syslog(syslog.LOG_INFO, "Notification sent - VNA Tenant ID: " + tenant_id)

    # REST-API method POST /api/tenants/<tenant_id>/flows/import is called within payload the workflow_generic_result.json file. <tenant_id> value is received into the HTTP Get Answer when calling REST-API api/users/me
        syslog.syslog(syslog.LOG_INFO, "API for importing the workflow to VNA - /management/api/tenants/{}/flows/import/")
        url = vna_url + "/management/api/tenants/{}/flows/import/".format(
            tenant_id)  # This URL contains the tenant_id and enable the import
        payload = data
        headers = {
            'Origin': vna_url,
            'Referer': vna_url + '/app/editor',
            'X-Requested-With': 'XMLHttpRequest',
            'Authorization': 'Basic anRyZWJhb2w6anRyZWJhb2w=',
            'Content-Type': 'application/json',
            'Cookie': 'JSESSIONID=8B4E6097CB90CE188EB443B4D95EE13A'
        }
        syslog.syslog(syslog.LOG_INFO, "URL: " + url)
        headers_str = str(headers)
        syslog.syslog(syslog.LOG_INFO, "Headers: " + headers_str)
        response = requests.request("POST", url, headers=headers, data=payload)
        response_str = str(response)
        syslog.syslog(syslog.LOG_INFO, "Notification sent - VNA Answer: " + response_str)
        json_response = json.loads(response.text)
        id = json_response["id"]
        payload = response.text
        #syslog.syslog(syslog.LOG_DEBUG, "Notification sent - VNA Answer: " + str(json_response))
        syslog.syslog(syslog.LOG_INFO, "Notification sent - VNA Worklow ID: " + id)

    # REST-API method PUT api/tenants/<tenant_id>/flows/<id>/imported is called within path <id> value received from REST-API /api/tenants/<tenant_id>/flows/import for validating  the VNA Workflow import
        syslog.syslog(syslog.LOG_INFO, "API for importing the workflow to VNA - /management/api/tenants/{}/flows/{}/imported")
        url = vna_url + "/management/api/tenants/{}/flows/{}/imported".format(
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
        syslog.syslog(syslog.LOG_INFO, "URL: " + url)
        headers_str = str(headers)
        syslog.syslog(syslog.LOG_INFO, "Headers: " + headers_str)
        #syslog.syslog(syslog.LOG_DEBUG, "Payload: " + payload)
        response = requests.request("PUT", url, headers=headers, data=payload)
        response_str = str(response)
        syslog.syslog(syslog.LOG_INFO, "Notification sent - VNA Answer: " + response_str)
        if response.status_code == 200:
            syslog.syslog(syslog.LOG_INFO, "Notification sent - VNA Answer: 200 OK")
            print("VNA Workflow registering in progress")
        elif response.status_code == 400:
            syslog.syslog(syslog.LOG_INFO, "Notification sent - VNA Answer: 400 - Workflow with same name already exists.")
            print("VNA Workflow already register")
        else:
            syslog.syslog(syslog.LOG_INFO, "Notification sent - Rest-API call failure")
            print("VNA Workflow registering failed")

    # REST-API method PUT /api/tenants/<tenant_id>/flows/<id>/deploy is called for enabling the VNA Workflow
        syslog.syslog(syslog.LOG_INFO, "API for enabling the workflow - /management/api/tenants/{}/flows/{}/deploy")
        url = vna_url + "/management/api/tenants/{}/flows/{}/deploy".format(
            tenant_id, id)
        syslog.syslog(syslog.LOG_INFO, "URL: " + url)
        response = requests.request("PUT", url, headers=headers, data=payload)
        response_str = str(response)
        syslog.syslog(syslog.LOG_INFO, "Notification sent - VNA Answer: " + response_str)
        if response.status_code == 200:
            syslog.syslog(syslog.LOG_INFO, "Notification sent - VNA Answer: 200 OK")
            print("VNA Workflow deployed and enabled")
        elif response.status_code == 400:
            syslog.syslog(syslog.LOG_INFO, "Notification sent - VNA Answer: 400 - Workflow already deployed - script exit")
            print("VNA Workflow already deployed")
            sys.exit()
        else:
            syslog.syslog(syslog.LOG_INFO, "Notification sent - Rest-API call failure")
            print("VNA Workflow depoyment failed")

    # REST-API for sending Welcome gif to Rainbow bubble
        syslog.syslog(syslog.LOG_INFO, "API for sending Welcome GIF to Rainbow Bubble/Rainhow JID")
        url = vna_url + "/api/flows/NBDNotif_File_{0}".format(company)
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
        syslog.syslog(syslog.LOG_INFO, "URL: " + url)
        headers_str = str(headers)
        syslog.syslog(syslog.LOG_INFO, "Headers: " + headers_str)
        response = requests.request("POST", url, headers=headers, data=payload)
        response_str = str(response)
        syslog.syslog(syslog.LOG_INFO, "Notification sent - VNA Answer: " + response_str)
        if response.status_code == 200:
            syslog.syslog(syslog.LOG_INFO, "Notification sent - VNA Answer: 200 OK")
            print("Rainbow bubble created")
        elif response.status_code == 400:
            syslog.syslog(syslog.LOG_INFO, "Notification sent - VNA Answer: 400 - Rainbow bubble send file failure.")
            print("Rainbow bubble aldready created")
        else:
            syslog.syslog(syslog.LOG_INFO, "Notification sent - Rest-API call failure")
            print("Rainbow bubble creation failed")

    else:
        print("There are no emails saved into the database")
        syslog.syslog(syslog.LOG_INFO, "There are no emails saved into the database - script exit")
        sys.exit()
except ValueError:
    print("There are no emails saved into the database")
    syslog.syslog(syslog.LOG_INFO, "Exception ValueError - script exit")        
    sys.exit()
except EOFError:
    print("There are no emails saved into the database")
    syslog.syslog(syslog.LOG_INFO, "Exception EOFError - script exit")   
    sys.exit()
except KeyboardInterrupt:
    print("User hits the interrupt key. Function set_called aborted")
    syslog.syslog(syslog.LOG_INFO, "Exception KeyboardInterrupt - script exit")   
    sys.exit()
