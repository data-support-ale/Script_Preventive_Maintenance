#!/usr/bin/env python3

import sys
import os
import re
import json
from mysql.connector import connect
from cryptography.fernet import Fernet
from time import strftime, localtime
import requests

print(sys.argv)

db_key=b'gP6lwSDvUdI04A8fC4Ib8PXEb-M9aTUbeZTBM6XAhpI='
dbsecret_password=b'gAAAAABivYWTJ-2OZQW4Ed2SGRNGayWRUIQZxLckzahNUoYSJBxsg5YZSYlMdiegdF1RCAvG4FqjMXD-nNeX0i6eD7bdFV8BEw=='
fernet = Fernet(db_key)
db_password = fernet.decrypt(dbsecret_password).decode()
database = connect(
		host='localhost',
		user='aletest',
		password=db_password,
		database='aledb'
		)
db = database.cursor()

# Aim of this script: notify ALE Admin that Preventive Maintenance setup is called and provides customer environment data. Automate the VNA Worklow deployment and Rainbow Bubble
#CHECK if Settings already added
query = "SELECT COUNT(*) FROM ALEUser_settings_value"
db.execute(query)

result = db.fetchall()[0][0]
print(result)

if result == 2:
    print("exit")
    sys.exit()

# Script init
script_name, switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company = sys.argv
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

path = os.path.dirname(__file__)

# Get informations from ALE_script.conf (mails, mails_raw, company name)

# mails_raw format: email_1;email_2;email_3
try:
    if mails != "":
        print(mails)
        url = "https://vna.preprod.omniaccess-stellar-asset-tracking.com/api/flows/NBDNotif_New_Bubble"
        headers = {'Content-type': 'application/json',
                "Accept-Charset": "UTF-8",
                'mails': '{0}'.format(mails),
                'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
                'company': '{0}'.format(company)
                 }
        response = requests.get(url, headers=headers)
        response = str(response.content)
        response = response.replace("b", "", 1)
        response = response.replace("\'", "", 2)
        print(response)
        room = response
        mail = re.sub(r";", '"}, {"email": "', mails)
        company = company

        settings = {
            'switch_user': switch_user, 
            'switch_password': switch_password,
            'mails': mails,
            'jid1': jid1,
            'jid2': jid2,
            'jid3': jid3,
            'ip_server': ip_server,
            'login_AP': login_AP,
            'pass_AP': pass_AP,
            'tech_pass': tech_pass,
            'random_id': random_id,
            'company': company,
            'room_id': room
        }

        settings_str = json.dumps(json.dumps(settings))
        query = "INSERT INTO ALEUser_settings_value VALUES (2,'SETTINGS'," + settings_str +  ")"
        db.execute(query)

        # Save (commit) the changes
        database.commit()


        # Notification sent to ALE admin for notifying ALE Admin on a dedicated Rainbow bubble that a setup init is called
        subject = (
            "NBD Preventive Maintenance - There is a new Setup, End Customer: \"{0}\"").format(company)
        body = "Attached to this message the configuration file, please setup the VNA accordingly"
        url = "https://vna.preprod.omniaccess-stellar-asset-tracking.com/api/flows/NBDNotif_Setup_File"
        headers = {
            'Content-type': "text/plain",
            'Content-Disposition': "attachment;filename=settings.conf",
            'jid1': '{0}'.format(jid1),
            'toto': '{0}'.format(subject),
            'tata': '{0}'.format(body)
        }
        # ALE_Script.conf is attached in the ALE Admin Rainbow bubble
        
        file = {'file': ('settings.conf', settings_str)}
        response = requests.post(url, files=file, headers=headers)

    # All generic fields (Rainbow bubble, emails, workflow name) are replaced based on ALE_script.conf file and Room_ID received from api/flows/NBDNotif_New_Bubble
        with open(path + "/VNA_Workflow/json/workflow_generic.json", "r", errors='ignore') as file_json:
            json_result = str(file_json.read())
            json_result = re.sub(r"\$email", mail, json_result)
            json_result = re.sub(r"\$company", company, json_result)
        with open(path + "/VNA_Workflow/json/workflow_generic_result.json", "w") as file_json:
            file_json.write(json_result)
        with open(path + "/VNA_Workflow/json/workflow_generic_result.json", "r") as file_json:
            data_json = json.load(file_json)

    # REST-API method GET for Login to VNA
        url = "https://vna.preprod.omniaccess-stellar-asset-tracking.com/management/api/users/me"
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
        url = "https://vna.preprod.omniaccess-stellar-asset-tracking.com/management/api/tenants/{}/flows/import/".format(
            tenant_id)  # This URL contains the tenant_id and enable the import
        headers = {
            'User-Agent':'Python Setup script',
            'Origin': 'https://vna.preprod.omniaccess-stellar-asset-tracking.com',
            'Referer': 'https://vna.preprod.omniaccess-stellar-asset-tracking.com/app/editor',
            'X-Requested-With': 'XMLHttpRequest',
            'Authorization': 'Basic anRyZWJhb2w6anRyZWJhb2w=',
            'Content-Type': 'application/json',
            'Cookie': 'JSESSIONID=8B4E6097CB90CE188EB443B4D95EE13A',
            'Accept': 'application/json, text/plain, */*'
        }
        response = requests.request("POST", url, headers=headers, json=data_json)
        json_response = json.loads(response.text)
        id = json_response["id"]
        payload = response.text

    # REST-API method PUT api/tenants/<tenant_id>/flows/<id>/imported is called within path <id> value received from REST-API /api/tenants/<tenant_id>/flows/import for validating  the VNA Workflow import
        url = "https://vna.preprod.omniaccess-stellar-asset-tracking.com/management/api/tenants/{}/flows/{}/imported".format(
            tenant_id, id)  # This URL validate the import use the tenant_id but also the import_id from the import request
        # replacement of different fields to specify the IDs in the .json before sending it out
        data_json = json.loads(payload)
        headers = {
            'Authorization': 'Basic anRyZWJhb2w6anRyZWJhb2w=',
            'Content-Type': 'application/json',
            'Cookie': 'JSESSIONID=80E64766B76B28CBFF0B44B3876ADA01'
        }
        response = requests.request("PUT", url, headers=headers, json=data_json)
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
        url = "https://vna.preprod.omniaccess-stellar-asset-tracking.com/management/api/tenants/{}/flows/{}/deploy".format(
            tenant_id, id)
        response = requests.request("PUT", url, headers=headers, json=data_json)
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
        url = "https://vna.preprod.omniaccess-stellar-asset-tracking.com/api/flows/NBDNotif_File_{0}".format(
            company)
        payload = open(path + "/VNA_Workflow/images/giphy.gif", "rb")
        # headers = {
        #     'jid1': '{0}'.format(jid1),
        #     'toto': 'Welcome to the Club',
        #     'Authorization': 'Basic anRyZWJhb2w6anRyZWJhb2w=',
        #     'Content-Type': 'image/gif'
        # }

        headers = {
            'Authorization': 'Basic anRyZWJhb2w6anRyZWJhb2w=',
            'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
            'Content-Type': 'image/gif',
            'jid1': '{0}'.format(jid1),
            'roomid': '{0}'.format(room),
            'subject': '{0}'.format('sending Welcome gif to Rainbow bubble'),
            'action': '{0}'.format('Welcome to the Club'),
            'result': '{0}'.format('Status: Success'),
            'email': '0'
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
