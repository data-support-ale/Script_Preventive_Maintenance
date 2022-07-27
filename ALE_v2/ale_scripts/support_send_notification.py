#!/usr/bin/env python3

import sys
import os
import requests
from time import strftime, localtime
import re
import json
# from database_conf import *

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
path = os.path.dirname(__file__)

def get_credentials():
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
    from mysql.connector import connect
    from cryptography.fernet import Fernet
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
    query = "SELECT * FROM ALEUser_settings_value"
    db.execute(query)
    result = json.loads(db.fetchall()[1][2])
    return result.values()


# Gathering of user settings
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company, room_id = get_credentials()

#######################################
#### New API's ########################
#######################################


def send_message_detailed(info, jid1, jid2, jid3):
    """ 
    Send the message in info to a Rainbowbot. This bot will send this message to the jid in parameters
    """

    text = info.split("\n")

    text += ["."]
    for _ in range(len(text), 10):
        text += [""]

    url = "https://vna.preprod.omniaccess-stellar-asset-tracking.com/api/flows/NBDNotif_Classic_{0}".format(company)
    headers = {
        'Content-type': 'application/json', 
        "Accept-Charset": "UTF-8",
        'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
        'roomid' : '{0}'.format(room_id),
        'jid1': '{0}'.format(jid1),
        'jid2': '{0}'.format(jid2),
        'jid3': '{0}'.format(jid3),              
        'text1': '{0}'.format(text[0]),
        'text2': '{0}'.format(text[1]), 
        'text3': '{0}'.format(text[2]), 
        'text4': '{0}'.format(text[3]), 
        'text5': '{0}'.format(text[4]), 
        'text6': '{0}'.format(text[5]), 
        'text7': '{0}'.format(text[6]), 
        'text8': '{0}'.format(text[7]), 
        'text9': '{0}'.format(text[8]), 
        'card': '0',
        'email': '0',
        'advanced': '0'
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        code = re.findall(r"<Response \[(.*?)\]>", str(response))
        if "200" in code:
            os.system('logger -t montag -p user.info 200 OK')
            print("Response  Text from VNA")
            value = response.text
            print(value)
            print(code)
            pass
        else:
            os.system('logger -t montag -p user.info REST API Timeout')
            pass
    except requests.exceptions.ConnectionError as response:
        print(response)
    except requests.exceptions.Timeout as response:
        print("Request Timeout when calling URL: " + url)
        print(response)
    except requests.exceptions.TooManyRedirects as response:
        print("Too Many Redirects when calling URL: " + url)
        print(response)
    except requests.exceptions.RequestException as response:
        print("Request exception when calling URL: " + url)
        print(response)

def send_alert_detailed(info, jid1, jid2, jid3, action, result, company):
    """
    Send the alert in info to a Rainbowbot. This bot will send this message to the jid in parameters
    """
    url = "https://vna.preprod.omniaccess-stellar-asset-tracking.com/api/flows/NBDNotif_Alert_{0}".format(company)
    headers = {
        'Content-type': 'application/json', 
        "Accept-Charset": "UTF-8",
        'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
        'roomid' : '{0}'.format(room_id),
        'jid1': '{0}'.format(jid1),
        'jid2': '{0}'.format(jid2),
        'jid3': '{0}'.format(jid3),              
        'subject': '{0}'.format(action),
        'action': '{0}'.format(info),
        'result': '{0}'.format(result),
        'card': '0',
        'email': '0',
        'advanced': '0'
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        code = re.findall(r"<Response \[(.*?)\]>", str(response))
        if "200" in code:
            os.system('logger -t montag -p user.info 200 OK')
            print("Response  Text from VNA")
            value = response.text
            print(value)
            print(code)
        else:
            os.system('logger -t montag -p user.info REST API Timeout')
            pass
    except requests.exceptions.ConnectionError as response:
        print(response)
    except requests.exceptions.Timeout as response:
        print("Request Timeout when calling URL: " + url)
        print(response)
    except requests.exceptions.TooManyRedirects as response:
        print("Too Many Redirects when calling URL: " + url)
        print(response)
    except requests.exceptions.RequestException as response:
        print("Request exception when calling URL: " + url)
        print(response)
        
def send_message_request_detailed(info, jid1, jid2, jid3):
    """ 
    Send the message, with a URL requests  to a Rainbowbot. This bot will send this message and request to the jid in parameters
    """

    text = info.split("\n")
    if len(text) == 1:
        text += [".", "", "", "", "", "", "", ""]
    else:
        for _ in range(len(text), 10):
            text += [""]

    try:
        url = "https://vna.preprod.omniaccess-stellar-asset-tracking.com/api/flows/NBDNotif_Classic_{0}".format(company)
        headers = {
            'Content-type': 'application/json', 
            "Accept-Charset": "UTF-8",
            'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
            'roomid' : '{0}'.format(room_id),
            'jid1': '{0}'.format(jid1),
            'jid2': '{0}'.format(jid2),
            'jid3': '{0}'.format(jid3),              
            'text1': '{0}'.format(text[0]),
            'text2': '{0}'.format(text[1]), 
            'text3': '{0}'.format(text[2]), 
            'text4': '{0}'.format(text[3]), 
            'text5': '{0}'.format(text[4]), 
            'text6': '{0}'.format(text[5]), 
            'text7': '{0}'.format(text[6]), 
            'text8': '{0}'.format(text[7]), 
            'text9': '{0}'.format(text[8]), 
            'Card': '1',
            'Email': '0',
            'Advanced': '0'
        }

        print(runtime)
        response = requests.get(url, headers=headers, timeout=600)
        print("Response from VNA")
        print(runtime)
        print(response)

        code = re.findall(r"<Response \[(.*?)\]>", str(response))
        if "200" in code:
            os.system('logger -t montag -p user.info 200 OK')
            print("Response  Text from VNA")
            value = response.text
            print(value)
            pass
        else:
            os.system('logger -t montag -p user.info REST API Timeout')
            info = "No answer received from VNA/Rainbow application - Answer Yes set by default"
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            value = "1"
    except requests.exceptions.ConnectionError as response:
        print(response)
        value = "1"
    except requests.exceptions.Timeout as response:
        print("Request Timeout when calling URL: " + url)
        print(response)
        value = "1"
    except requests.exceptions.TooManyRedirects as response:
        print("Too Many Redirects when calling URL: " + url)
        print(response)
        value = "1"
    except requests.exceptions.RequestException as response:
        print("Request exception when calling URL: " + url)
        print(response)
        value = "1"
    return value

def send_file_detailed(subject, jid1, action, result, company, filename_path):
        """ 
            Send the attachement to a Rainbowbot. This bot will send this file to the jid in parameters
        """					  
        url = "https://vna.preprod.omniaccess-stellar-asset-tracking.com/api/flows/NBDNotif_File_{0}".format(company)
        headers = {
            'Content-type': "text/plain",
            'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
            'Content-Disposition': "attachment;filename=troubleshooting.log", 									  
            'jid1': '{0}'.format(jid1),
            'roomid': '{0}'.format(room_id), 
            'subject': '{0}'.format(subject),
            'action': '{0}'.format(action),
            'result': '{0}'.format(result),
            'Email': '0'
        }
        try:
           files = {'file': open(filename_path, 'r')}
        except:
           pass
        try:
            response = requests.post(url, files=files, headers=headers, timeout=20)
															   
            code = re.findall(r"<Response \[(.*?)\]>", str(response))
            if "200" in code:
                os.system('logger -t montag -p user.info 200 OK')
                print("Response  Text from VNA")
                value = response.text
                print(value)
                print(code)
            else:
                os.system('logger -t montag -p user.info REST API Timeout')
                pass
        except requests.exceptions.ConnectionError as response:
            print(response)
        except requests.exceptions.Timeout as response:
            print("Request Timeout when calling URL: " + url)
            print(response)
        except requests.exceptions.TooManyRedirects as response:
            print("Too Many Redirects when calling URL: " + url)
            print(response)
        except requests.exceptions.RequestException as response:
            print("Request exception when calling URL: " + url)
            print(response)


def send_message_request_advanced(info, jid1, jid2, jid3, feature):
    """ 
    Send the message, with a URL requests  to a Rainbowbot. This bot will send this message and request to the jid in parameters
    """
    text = info.split("\n")
    if len(text) == 1:
        text += [".", "", "", "", "", "", "", ""]
    else:
        for _ in range(len(text), 10):
            text += [""]

    if feature != "":
        try:

            url = "https://vna.preprod.omniaccess-stellar-asset-tracking.com/api/flows/NBDNotif_Classic_"+company
            headers = {
                'Content-type': 'application/json', 
                "Accept-Charset": "UTF-8",
                'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
                'roomid' : '{0}'.format(room_id),
                'jid1': '{0}'.format(jid1),
                'jid2': '{0}'.format(jid2),
                'jid3': '{0}'.format(jid3),              
                'text1': '{0}'.format(text[0]),
                'text2': '{0}'.format(text[1]), 
                'text3': '{0}'.format(text[2]), 
                'text4': '{0}'.format(text[3]), 
                'text5': '{0}'.format(text[4]), 
                'text6': '{0}'.format(text[5]), 
                'text7': '{0}'.format(text[6]), 
                'text8': '{0}'.format(text[7]), 
                'text9': '{0}'.format(text[8]), 
                'Card': '2',
                'Email': '0',
                'Advanced': '{0}'.format(feature)
            }

            print(runtime)
            response = requests.get(url, headers=headers, timeout=600)
            print("Response from VNA")
            print(runtime)
            print(response)

            code = re.findall(r"<Response \[(.*?)\]>", str(response))
            if "200" in code:
                os.system('logger -t montag -p user.info 200 OK')
                print("Response  Text from VNA")
                value = response.text
                print(value)
            else:
                os.system('logger -t montag -p user.info REST API Timeout')
                info = "No answer received from VNA/Rainbow application - Answer Yes set by default"
                # send_message_detailed(info, jid1, jid2, jid3)
                send_message_detailed(info, jid1, jid2, jid3)
                value = "1"
        except requests.exceptions.ConnectionError as response:
            print(response)
            value = "1"
        except requests.exceptions.Timeout as response:
            print("Request Timeout when calling URL: " + url)
            print(response)
            value = "1"
        except requests.exceptions.TooManyRedirects as response:
            print("Too Many Redirects when calling URL: " + url)
            print(response)
            value = "1"
        except requests.exceptions.RequestException as response:
            print("Request exception when calling URL: " + url)
            print(response)
            value = "1"
    else:
        print("feature variable empty")
        sys.exit()

    return value


if __name__ == "__main__":
    switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company, room_id = get_credentials()
    send_message_detailed("1\n2\n3\n4", jid1, jid2, jid3)
    send_message_request_detailed("1\n2\n3\n4", jid1, jid2, jid3)
    send_message_request_advanced("1\n2\n3\n4", jid1, jid2, jid3, "TEST")
    
