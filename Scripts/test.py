#!/usr/local/bin/python3.7

import sys
import os
#from support_tools_OmniSwitch import get_credentials
from time import strftime, localtime
import requests
import re

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
path = "/opt/ALE_Script"
# Get informations from logs.

def get_credentials(attribute=None):
    """
    This function collects all the information about the switch's credentials in the log.
    It collects also the information usefull for  notification sender in the file ALE_script.conf.

    :param:                         None
    :return str user:               Switch user login
    :return str password:           Switch user password
    :return str jid:                 Rainbow JID  of recipients
    :return str gmail_usr:          Sender's email userID
    :return str gmail_passwd:       Sender's email password
    :return str mails:              List of email addresses of recipients
    """

    with open(path + "/ALE_script.conf", "r") as content_variable:
        login_switch, pass_switch, mails, rainbow_jid1, rainbow_jid2, rainbow_jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company, room_id, * \
            kargs = re.findall(
                r"(?:,|\n|^)(\"(?:(?:\"\")*[^\"]*)*\"|[^\",\n]*|(?:\n|$))", str(content_variable.read()))
        if attribute == None:
            return login_switch, pass_switch, mails, rainbow_jid1, rainbow_jid2, rainbow_jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company
        elif attribute == "company":
            return company
        elif attribute == "room_id":
            return room_id
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

# If we put argument when calling the script we can test different Workflows (companies)
if sys.argv[1] != None:
    company = sys.argv[1]
    room_id = get_credentials("room_id")
    print(company)
    url = ("https://vna.preprod.omniaccess-stellar-asset-tracking.com/api/flows/NBDNotif_File_{0}").format(company)
    payload = open(path + "/VNA_Workflow/images/giphy.gif", "rb")
    headers = {
        'Content-Type': 'image/gif',
        'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
        'Authorization': 'Basic anRyZWJhb2w6anRyZWJhb2w=',
        'Content-Disposition': 'attachment; filename=welcome.gif',
        'roomid' : '{0}'.format(room_id),
        'jid1': '{0}'.format(jid1),
        'subject': '{0}'.format("Testing"),
        'action': '{0}'.format("NBD Preventive Maintenance - This is a test!"),
        'result': '{0}'.format("Status: GIF Sent"),
        'Email': '0'
    }
    try:
        response = requests.request("POST", url, headers=headers, data=payload, timeout=60)
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
