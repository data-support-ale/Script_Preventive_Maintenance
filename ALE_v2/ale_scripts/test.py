#!/usr/bin/env python3

import sys
import os
from support_tools_OmniSwitch import get_credentials
from time import strftime, localtime
import requests
import re

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company, room_id = get_credentials()

# If we put argument when calling the script we can test different Workflows (companies)


if sys.argv[1] != None:
    company = sys.argv[1]
    print(company)
    info = "NBD Preventive Maintenance - This is a test!"
    url = ("https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Classic_{0}").format(company)
    headers = {
        'Content-type': 'application/json', 
        "Accept-Charset": "UTF-8",
        'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
        'jid1': '{0}'.format(jid1),
        'jid2': '{0}'.format(jid2),
        'jid3': '{0}'.format(jid3),              
        'subject': '{0}'.format("Testing"),
        'action': '{0}'.format(info),
        'result': '{0}'.format("Status: Success"),
        'Card': '0',
        'Email': '0',
        'Advanced': '0'
    }
    try:
        response = requests.get(url, headers=headers, timeout=60)
        code = re.findall(r"<Response \[(.*?)\]>", str(response)) 
        print(code)
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
    payload = open("/opt/ALE_Script/VNA_Workflow/images/giphy.gif", "rb")
    # headers = {
    #     'jid1': '{0}'.format(jid1),
    #     'toto': '{0}'.format(info),
    #     'Authorization': 'Basic anRyZWJhb2w6anRyZWJhb2w=',
    #     'Content-Type': 'image/gif',
    #     'Content-Disposition': 'attachment; filename=welcome.gif'
    # }
    headers = {
        'Content-Type': 'image/gif',
        'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
        'Authorization': 'Basic anRyZWJhb2w6anRyZWJhb2w=',
        'Content-Disposition': 'attachment; filename=welcome.gif', 
        'jid1': '{0}'.format(jid1), 
        'subject': '{0}'.format("Testing"),
        'action': '{0}'.format(info),
        'result': '{0}'.format("Status: GIF Sent"),
        'Email': '0'
    }
    try:
        response = requests.request(
            "POST", url, headers=headers, data=payload, timeout=60)
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
