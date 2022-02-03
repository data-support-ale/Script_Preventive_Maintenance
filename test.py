#!/usr/bin/env python3

import sys
import os
from support_tools_OmniSwitch import get_credentials
from time import strftime, localtime
import requests


# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user,switch_password,mails,jid,ip_server,login_AP,pass_AP,tech_pass,random_id,company = get_credentials()

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
    try:
        response = requests.get(url, headers=headers,timeout=60)
        if "200" in code:
            os.system('logger -t montag -p user.info 200 OK')
            print("Response  Text from VNA")
            value = response.text
            print(value)
        else:
            os.system('logger -t montag -p user.info REST API Timeout')    
    except requests.exceptions.ConnectionError:
        pass
    except requests.exceptions.Timeout:
        print("Request Timeout when calling URL: " + url)
        pass  
    except requests.exceptions.TooManyRedirects:
        print("Too Many Redirects when calling URL: " + url)
        pass
    except requests.exceptions.RequestException:
        print("Request exception when calling URL: " + url)
        pass

    url = ("https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_File_{0}").format(company)
    payload=open("/opt/ALE_Script/VNA_Workflow/images/giphy.gif", "rb")
    headers = {
              'jid1': '{0}'.format(jid),
              'toto': '{0}'.format(info),
              'Authorization': 'Basic anRyZWJhb2w6anRyZWJhb2w=',
              'Content-Type': 'image/gif',
              'Content-Disposition' : 'attachment; filename=welcome.gif'
              }    
    try:
        response = requests.request("POST", url, headers=headers, data=payload,timeout=60)
        if "200" in code:
            os.system('logger -t montag -p user.info 200 OK')
            print("Response  Text from VNA")
            value = response.text
            print(value)
        else:
            os.system('logger -t montag -p user.info REST API Timeout')    
    except requests.exceptions.ConnectionError:
        pass
    except requests.exceptions.Timeout:
        print("Request Timeout when calling URL: " + url)
        pass  
    except requests.exceptions.TooManyRedirects:
        print("Too Many Redirects when calling URL: " + url)
        pass
    except requests.exceptions.RequestException:
        print("Request exception when calling URL: " + url)
        pass

else:
    print("Please provide Company name in argument when executing this script")
