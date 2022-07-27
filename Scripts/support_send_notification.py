#!/usr/local/bin/python3.7

import sys
import os
import requests
from time import strftime, localtime
import re
# from database_conf import *
import syslog

syslog.openlog('support_send_notification')

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
dir="/opt/ALE_Script"
site = "https://vna.preprod.omniaccess-stellar-asset-tracking.com"


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

    with open(dir + "/ALE_script.conf", "r") as content_variable:
        login_switch, pass_switch, mails, rainbow_jid1, rainbow_jid2, rainbow_jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company, room_id, * \
            kargs = re.findall(
                r"(?:,|\n|^)(\"(?:(?:\"\")*[^\"]*)*\"|[^\",\n]*|(?:\n|$))", str(content_variable.read()))
        if attribute == None:
            return login_switch, pass_switch, mails, rainbow_jid1, rainbow_jid2, rainbow_jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company
        elif attribute == "login_switch":
            return login_switch
        elif attribute == "pass_switch":
            return pass_switch
        elif attribute == "mails":
            return mails
        elif attribute == "rainbow_jid":
            return [rainbow_jid1, rainbow_jid2, rainbow_jid3]
        elif attribute == "ip_server":
            return ip_server
        elif attribute == "login_AP":
            return login_AP
        elif attribute == "pass_AP":
            return pass_AP
        elif attribute == "tech_pass":
            return tech_pass
        elif attribute == "random_id":
            return random_id
        elif attribute == "company":
            return company
        elif attribute == "room_id":
            return room_id



room_id = get_credentials("room_id")
company = get_credentials("company")
jid1, jid2, jid3 = get_credentials("rainbow_jid")


#######################################
#### New API's ########################
#######################################


def send_message_detailed(info):
    """ 
    Send the message in info to a Rainbowbot. This bot will send this message to the jid in parameters
    """

    text = info.split("\n")

    text += ["."]
    for _ in range(len(text), 10):
        text += [""]

    url = site + "/api/flows/NBDNotif_Classic_{0}".format(company)
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
    syslog.syslog(syslog.LOG_INFO, "URL: " + url)
    syslog.syslog(syslog.LOG_INFO, "Headers: " + str(headers))
    try:
        syslog.syslog(syslog.LOG_INFO, "Calling VNA API - send_message - method GET")
        response = requests.get(url, headers=headers, timeout=5)
        syslog.syslog(syslog.LOG_INFO, "Notification sent - VNA Answer: " + str(response))
        code = re.findall(r"<Response \[(.*?)\]>", str(response))
        if "200" in code:
            syslog.syslog(syslog.LOG_INFO, "VNA Answer HTTP 200 OK")
            print("Response  Text from VNA")
            value = response.text
            syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
            print(value)
            print(code)
            pass
        elif "404" in code:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call - Internal Server Error")
            value = response.text
            syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
        elif "401" in code:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call - Authentication failed")
            value = response.text
            syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
        elif "408" in code:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call - Timeout")
            value = response.text
            syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
        else:
            syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
        pass
    except requests.exceptions.ConnectionError as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Connection Error - " + str(response))
        print(response)
    except requests.exceptions.Timeout as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Timeout - " + str(response))
        print("Request Timeout when calling URL: " + url)
        print(response)
    except requests.exceptions.TooManyRedirects as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: TooManyRedirects - " + str(response))
        print("Too Many Redirects when calling URL: " + url)
        print(response)
    except requests.exceptions.RequestException as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: " + str(response))
        print("Request exception when calling URL: " + url)
        print(response)

def send_alert_detailed(subject, action, result):
    """
    Send the alert in info to a Rainbowbot. This bot will send this message to the jid in parameters
    """
    url = site + "/api/flows/NBDNotif_Alert_{0}".format(company)
    headers = {
        'Content-type': 'application/json', 
        "Accept-Charset": "UTF-8",
        'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
        'roomid' : '{0}'.format(room_id),
        'jid1': '{0}'.format(jid1),
        'jid2': '{0}'.format(jid2),
        'jid3': '{0}'.format(jid3),              
        'subject': '{0}'.format(subject),
        'action': '{0}'.format(action),
        'result': '{0}'.format(result),
        'card': '0',
        'email': '0',
        'advanced': '0'
    }
    syslog.syslog(syslog.LOG_INFO, "URL: " + url)
    syslog.syslog(syslog.LOG_INFO, "Headers: " + str(headers))
    try:
        syslog.syslog(syslog.LOG_INFO, "Calling VNA API - send_alert - method GET")
        response = requests.get(url, headers=headers, timeout=5)
        syslog.syslog(syslog.LOG_INFO, "Notification sent - VNA Answer: " + str(response))
        code = re.findall(r"<Response \[(.*?)\]>", str(response))
        if "200" in code:
            syslog.syslog(syslog.LOG_INFO, "VNA Answer HTTP 200 OK")
            print("Response  Text from VNA")
            value = response.text
            syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
            print(value)
            print(code)
        elif "404" in code:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call - Internal Server Error")
            value = response.text
            syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
        elif "401" in code:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call - Authentication failed")
            value = response.text
            syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
        elif "408" in code:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call - Timeout")
            value = response.text
            syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
        else:
            syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
            pass
    except requests.exceptions.ConnectionError as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Connection Error - " + str(response))
        print(response)
    except requests.exceptions.Timeout as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Timeout - " + str(response))
        print("Request Timeout when calling URL: " + url)
        print(response)
    except requests.exceptions.TooManyRedirects as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: TooManyRedirects - " + str(response))
        print("Too Many Redirects when calling URL: " + url)
        print(response)
    except requests.exceptions.RequestException as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: " + str(response))
        print("Request exception when calling URL: " + url)
        print(response)
        
def send_message_request_detailed(info):
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
        url = site + "/api/flows/NBDNotif_Classic_{0}".format(company)
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
        syslog.syslog(syslog.LOG_INFO, "URL: " + url)
        syslog.syslog(syslog.LOG_INFO, "Headers: " + str(headers))
        print("Sending request")
        syslog.syslog(syslog.LOG_INFO, "Calling VNA API - send_message_request - method GET")
        response = requests.get(url, headers=headers, timeout=600)
        print("Response from VNA")
        print(response)
        syslog.syslog(syslog.LOG_INFO, "Notification sent - VNA Answer: " + str(response))
        code = re.findall(r"<Response \[(.*?)\]>", str(response))
        if "200" in code:
            print("Response  Text from VNA")
            value = response.text
            syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
            print(value)
            pass
        elif "404" in code:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call - Internal Server Error")
            value = response.text
            syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
        elif "401" in code:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call - Authentication failed")
            value = response.text
            syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
        elif "408" in code:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call - Timeout")
            value = response.text
            syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
        else:
            syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Timeout")
            notif = "No answer received from VNA/Rainbow application - Answer Yes set by default"
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
            send_message_detailed(notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            syslog.syslog(syslog.LOG_INFO, "Value set to 1")
            value = "1"
    except requests.exceptions.ConnectionError as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Connection Error - " + str(response))
        print(response)
        syslog.syslog(syslog.LOG_INFO, "Value set to 1")
        value = "1"
    except requests.exceptions.Timeout as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Timeout - " + str(response))
        print(response)
        syslog.syslog(syslog.LOG_INFO, "Value set to 1")
        value = "1"
    except requests.exceptions.TooManyRedirects as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: TooManyRedirects - " + str(response))
        print(response)
        syslog.syslog(syslog.LOG_INFO, "Value set to 1")
        value = "1"
    except requests.exceptions.RequestException as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: " + str(response))
        print(response)
        syslog.syslog(syslog.LOG_INFO, "Value set to 1")
        value = "1"
    return value

def send_file_detailed(filename_path, subject, action, result, category):
        """ 
            Send the attachement to a Rainbowbot. This bot will send this file to the jid in parameters
        """				  
        url = site + "/api/flows/NBDNotif_File_{0}".format(company)
        headers = {
            'Content-type': "text/plain",
            'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
            'Content-Disposition': ("attachment;filename={0}.log").format(category), 									  
            'jid1': '{0}'.format(jid1),
            'roomid': '{0}'.format(room_id), 
            'subject': '{0}'.format(subject),
            'action': '{0}'.format(action),
            'result': '{0}'.format(result),
            'Email': '0'
        }
        try:
            files = {'file': open(filename_path, 'r')}
            syslog.syslog(syslog.LOG_DEBUG, "Payload: " + str(files))
        except FileNotFoundError as exception:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: FileNotFoundError - " + str(exception))
            filename_path = "/var/log/server/support_send_notification.log"
            files = {'file': open(filename_path, 'r')}
            syslog.syslog(syslog.LOG_DEBUG, "Payload: " + str(files))
            pass          
        except  UnboundLocalError as exception:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: UnboundLocalError - " + str(exception))
            pass 
        try:
            syslog.syslog(syslog.LOG_INFO, "URL: " + url)
            syslog.syslog(syslog.LOG_INFO, "Headers: " + str(headers))
            print("Sending request")
            syslog.syslog(syslog.LOG_INFO, "Calling VNA API - send_file - method POST")
            response = requests.post(url, files=files, headers=headers, timeout=20)
            syslog.syslog(syslog.LOG_INFO, "Notification sent - VNA Answer: " + str(response))															   
            code = re.findall(r"<Response \[(.*?)\]>", str(response))
            if "200" in code:
                syslog.syslog(syslog.LOG_INFO, "VNA Answer HTTP 200 OK")
                print("Response  Text from VNA")
                value = response.text
                syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
                print(value)
                print(code)
            elif "404" in code:
                syslog.syslog(syslog.LOG_INFO, "VNA API Call - Internal Server Error")
                value = response.text
                syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
            elif "401" in code:
                syslog.syslog(syslog.LOG_INFO, "VNA API Call - Authentication failed")
                value = response.text
                syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
            elif "408" in code:
                syslog.syslog(syslog.LOG_INFO, "VNA API Call - Timeout")
                value = response.text
                syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
            else:
                syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
                pass
        except requests.exceptions.ConnectionError as response:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Connection Error - " + str(response))
            print(response)
        except requests.exceptions.Timeout as response:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Timeout - " + str(response))
            print("Request Timeout when calling URL: " + url)
            print(response)
        except requests.exceptions.TooManyRedirects as response:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: TooManyRedirects - " + str(response))
            print("Too Many Redirects when calling URL: " + url)
            print(response)
        except requests.exceptions.RequestException as response:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: " + str(response))
            print("Request exception when calling URL: " + url)
            print(response)


def send_message_request_advanced(info, feature):
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
        syslog.syslog(syslog.LOG_INFO, "Rainbow Adaptive Card with 4th option: " + feature)
        try:

            url = site + "/api/flows/NBDNotif_Classic_"+company
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
            syslog.syslog(syslog.LOG_INFO, "URL: " + url)
            syslog.syslog(syslog.LOG_INFO, "Headers: " + str(headers))
            print("Sending request")
            syslog.syslog(syslog.LOG_INFO, "Calling VNA API - send_message_request_advanced - method GET")
            response = requests.get(url, headers=headers, timeout=600)
            syslog.syslog(syslog.LOG_INFO, "Notification sent - VNA Answer: " + str(response))
            print("Response from VNA")
            print(response)

            code = re.findall(r"<Response \[(.*?)\]>", str(response))
            if "200" in code:
                print("Response  Text from VNA")
                value = response.text
                syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
                print(value)
            elif "404" in code:
                syslog.syslog(syslog.LOG_INFO, "VNA API Call - Internal Server Error")
                value = response.text
                syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
            elif "401" in code:
                syslog.syslog(syslog.LOG_INFO, "VNA API Call - Authentication failed")
                value = response.text
                syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
            elif "408" in code:
                syslog.syslog(syslog.LOG_INFO, "VNA API Call - Timeout")
                value = response.text
                syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
            else:
                syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Timeout")
                notif = "No answer received from VNA/Rainbow application - Answer Yes set by default"
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
                syslog.syslog(syslog.LOG_INFO, "Value set to 1")
                value = "1"
        except requests.exceptions.ConnectionError as response:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Connection Error - " + str(response))
            print(response)
            syslog.syslog(syslog.LOG_INFO, "Value set to 1")
            value = "1"
        except requests.exceptions.Timeout as response:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Timeout - " + str(response))
            print(response)
            syslog.syslog(syslog.LOG_INFO, "Value set to 1")
            value = "1"
        except requests.exceptions.TooManyRedirects as response:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: TooManyRedirects - " + str(response))
            print(response)
            syslog.syslog(syslog.LOG_INFO, "Value set to 1")
            value = "1"
        except requests.exceptions.RequestException as response:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: " + str(response))
            print(response)
            syslog.syslog(syslog.LOG_INFO, "Value set to 1")
            value = "1"
    else:
        print("feature variable empty")
        syslog.syslog(syslog.LOG_INFO, "Feature variable is empty - script exit")
        sys.exit()
    return value

def send_test(subject,action,result):
    """ 
    API for testing VNA and Rainbow reachability

    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :return:                        None
    """
    url = site + "/api/flows/NBDNotif_Test_"+company
    headers = {
                'Content-type': 'application/json', 
                "Accept-Charset": "UTF-8",
                'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
                'jid1': '{0}'.format(jid1),
                'roomid': '{0}'.format(room_id), 
                'subject': '{0}'.format(subject),
                'action': '{0}'.format(action),
                'result': '{0}'.format(result),
                'Card': '0',
               }
    syslog.syslog(syslog.LOG_INFO, "URL: " + url)
    syslog.syslog(syslog.LOG_INFO, "Headers: " + str(headers))
    try:
        syslog.syslog(syslog.LOG_INFO, "Calling VNA API - send_test - method GET")
        response = requests.get(url, headers=headers, timeout=0.5)
        syslog.syslog(syslog.LOG_INFO, "Notification sent - VNA Answer: " + str(response))
        code = re.findall(r"<Response \[(.*?)\]>", str(response))
        if "200" in code:
            syslog.syslog(syslog.LOG_INFO, "VNA Answer HTTP 200 OK")
            print("Response  Text from VNA")
            value = response.text
            syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
            print(value)
            print(code)
        elif "404" in code:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call - Internal Server Error")
            value = response.text
            syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
        elif "401" in code:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call - Authentication failed")
            value = response.text
            syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
        elif "408" in code:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call - Timeout")
            value = response.text
            syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
        else:
            syslog.syslog(syslog.LOG_INFO, "VNA value: " + response.text)
    except requests.exceptions.ConnectionError as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Connection Error - " + str(response))
        print(response)
    except requests.exceptions.Timeout as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Timeout - " + str(response))
        print("Request Timeout when calling URL: " + url)
        print(response)
    except requests.exceptions.TooManyRedirects as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: TooManyRedirects - " + str(response))
        print("Too Many Redirects when calling URL: " + url)
        print(response)
    except requests.exceptions.RequestException as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: " + str(response))
        print("Request exception when calling URL: " + url)
        print(response)

if __name__ == "__main__":
    try:
        switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()
        #send_message_detailed("1\n2\n3\n4")
        #send_message_request_detailed("1\n2\n3\n4")
        #send_message_request_advanced("1\n2\n3\n4", "TEST")
        action = result = ""
        subject = "Le vélo est le moyen de transport le plus démocratique. Le vélo est le plus audacieux, stimulant car il donne à son propriétaire le sentiment tentant de liberté, c'est pourquoi on peut dire sans aucune exagération, le vélo est un symbole de liberté."
        send_test(subject, action, result)
        subject = "Alerte canicule en Bretagne!"
        send_alert_detailed(subject, action, result)
        filename_path = ""
        subject = "Preventive Maintenance application - Ceci est un test"
        action = "Aucun resultat n est attendu"
        result = "Ni auncune action"
        category = "test"
        send_file_detailed(filename_path, subject, action, result, category)
    except (RuntimeError, TypeError, NameError):
        raise
    except OSError:
        raise
    except KeyboardInterrupt:
        syslog.syslog(syslog.LOG_INFO, "KeyboardInterrupt")
        raise
    finally:
        print("End of tests")
        syslog.syslog(syslog.LOG_INFO, "End of tests")
    
