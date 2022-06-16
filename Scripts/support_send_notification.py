#!/usr/local/bin/python3.7

from cProfile import run
from cgitb import text
from email import header
from operator import le
import sys
import requests
from time import sleep, strftime, localtime
import re
from database_conf import *

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())


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

    with open("/opt/ALE_Script/ALE_script.conf", "r") as content_variable:
        login_switch, pass_switch, mails, rainbow_jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company, room_id, * \
            kargs = re.findall(
                r"(?:,|\n|^)(\"(?:(?:\"\")*[^\"]*)*\"|[^\",\n]*|(?:\n|$))", str(content_variable.read()))
        if attribute == None:
            return login_switch, pass_switch, mails, rainbow_jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company
        elif attribute == "company":
            return company
        elif attribute == "room_id":
            return room_id



def send_message(info, jid):
    """ 
    Send the message in info to a Rainbowbot. This bot will send this message to the jid in parameters

    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :return:                        None
    """
    text = info.split("\n")

    text += ["."]
    for _ in range(len(text), 10):
        text += [""]


    company = get_credentials("company")
    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Classic_"+company
    headers = {
                'Content-type': 'application/json', 
                "Accept-Charset": "UTF-8",
                'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
                'jid1': '{0}'.format(jid), 
#                'jid2': '{0}'.format(jid2),
#                'jid3': '{0}'.format(jid3),
                'text1': '{0}'.format(text[0]),
                'text2': '{0}'.format(text[1]), 
                'text3': '{0}'.format(text[2]), 
                'text4': '{0}'.format(text[3]), 
                'text5': '{0}'.format(text[4]), 
                'text6': '{0}'.format(text[5]), 
                'text7': '{0}'.format(text[6]), 
                'text8': '{0}'.format(text[7]), 
                'text9': '{0}'.format(text[8]), 
#                'subject': '{0}'.format(action),
#                'action': '{0}'.format(info),
#                'result': '{0}'.format(result),
                'Card': '0',
#                'Email': '0',
#                'Advanced': '0'
               }
    try:
        response = requests.get(url, headers=headers, timeout=0.5)
        code = re.findall(r"<Response \[(.*?)\]>", str(response))
        if "200" in code:
            os.system('logger -t montag -p user.info 200 OK')
            print("Response  Text from VNA")
            value = response.text
            print(value)
            print(code)
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No", "Decision": "Success"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass
            pass
        else:
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass
            os.system('logger -t montag -p user.info REST API Timeout')
            pass
    except requests.exceptions.ConnectionError as response:
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
    except requests.exceptions.Timeout as response:
        print("Request Timeout when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
    except requests.exceptions.TooManyRedirects as response:
        print("Too Many Redirects when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
    except requests.exceptions.RequestException as response:
        print("Request exception when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass

def send_test(info, jid,company):
    """ 
    API for testing VNA and Rainbow reachability

    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :return:                        None
    """
    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Test_"+company
    headers = {
                'Content-type': 'application/json', 
                "Accept-Charset": "UTF-8",
                'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
                'jid1': '{0}'.format(jid), 
#                'jid2': '{0}'.format(jid2),
#                'jid3': '{0}'.format(jid3),
                'info': '{0}'.format(info), 
#                'subject': '{0}'.format(action),
#                'action': '{0}'.format(info),
#                'result': '{0}'.format(result),
                'Card': '0',
#                'Email': '0',
#                'Advanced': '0'
               }
    try:
        response = requests.get(url, headers=headers, timeout=0.5)
        code = re.findall(r"<Response \[(.*?)\]>", str(response))
        if "200" in code:
            os.system('logger -t montag -p user.info 200 OK')
            print("Response  Text from VNA")
            value = response.text
            print(value)
            print(code)
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No", "Decision": "Success"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass
            pass
        else:
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass
            os.system('logger -t montag -p user.info REST API Timeout')
            pass
    except requests.exceptions.ConnectionError as response:
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
    except requests.exceptions.Timeout as response:
        print("Request Timeout when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
    except requests.exceptions.TooManyRedirects as response:
        print("Too Many Redirects when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
    except requests.exceptions.RequestException as response:
        print("Request exception when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass

def send_alert(info, jid):
    """
    Send the message in info to a Rainbowbot. This bot will send this message to the jid in parameters

    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :return:                        None
    """
    company = get_credentials("company")
    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Alert_"+company
    headers = {
                'Content-type': 'application/json',
                "Accept-Charset": "UTF-8",
                'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
                'jid1': '{0}'.format(jid), 
                'subject': '{0}'.format(info), 
                'Card': '0'
                }
    try:
        response = requests.get(url, headers=headers, timeout=0.5)
        code = re.findall(r"<Response \[(.*?)\]>", str(response))
        if "200" in code:
            os.system('logger -t montag -p user.info 200 OK')
            print("Response  Text from VNA")
            value = response.text
            print(value)
            print(code)
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No", "Decision": "Success"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass
        else:
            os.system('logger -t montag -p user.info REST API Timeout')
            pass
    except requests.exceptions.ConnectionError as response:
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
    except requests.exceptions.Timeout as response:
        print("Request Timeout when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
    except requests.exceptions.TooManyRedirects as response:
        print("Too Many Redirects when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
    except requests.exceptions.RequestException as response:
        print("Request exception when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass

def send_message_request(info, jid):
    """ 
    Send the message, with a URL requests  to a Rainbowbot. This bot will send this message and request to the jid in parameters

    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :param str ip_server:           IP Adress of the server log , which is also a web server
    :param str id_client:           Unique ID creates during the Setup.sh, to identifie the URL request to the good client
    :param str id_case:             Unique ID creates during the response_handler , to identifie the URL request to the good case.
    :return:                        None
    """
 
    text = info.split("\n")
    if len(text) == 1:
        text += [".", "", "", "", "", "", "", ""]
    else:
        for _ in range(len(text), 10):
            text += [""]
 
    try:
        company = get_credentials("company")
        url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Classic_"+company
        headers = {
                    'Content-type': 'application/json', 
                    "Accept-Charset": "UTF-8",
                    'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
                    'jid1': '{0}'.format(jid),
                    'text1': '{0}'.format(text[0]),
                    'text2': '{0}'.format(text[1]), 
                    'text3': '{0}'.format(text[2]), 
                    'text4': '{0}'.format(text[3]), 
                    'text5': '{0}'.format(text[4]), 
                    'text6': '{0}'.format(text[5]), 
                    'text7': '{0}'.format(text[6]), 
                    'text8': '{0}'.format(text[7]), 
                    'text9': '{0}'.format(text[8]), 
                    'Card': '1'
                    }
        response = requests.get(url, headers=headers, timeout=600)
        print("Response from VNA")
        print(response)

        code = re.findall(r"<Response \[(.*?)\]>", str(response))
        if "200" in code:
            os.system('logger -t montag -p user.info 200 OK')
            print("Response  Text from VNA")
            value = response.text
            print(value)
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "Yes", "Decision": value}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
            pass                
        else:
            os.system('logger -t montag -p user.info REST API Timeout')
            info = "No answer received from VNA/Rainbow application - Answer Yes set by default"
            send_message(info, jid)
            value = "1"
    except requests.exceptions.ConnectionError as response:
        print(response)
        value = "1"
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "Yes"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
    except requests.exceptions.Timeout as response:
        print("Request Timeout when calling URL: " + url)
        print(response)
        value = "1"
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "Yes"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
    except requests.exceptions.TooManyRedirects as response:
        print("Too Many Redirects when calling URL: " + url)
        print(response)
        value = "1"
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "Yes"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
    except requests.exceptions.RequestException as response:
        print("Request exception when calling URL: " + url)
        print(response)
        value = "1"
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "Yes"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
    return value

def send_message_request_advanced(info, jid, feature):
    """ 
    Send the message, with a URL requests  to a Rainbowbot. This bot will send this message and request to the jid in parameters

    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :param str ip_server:           IP Adress of the server log , which is also a web server
    :param str id_client:           Unique ID creates during the Setup.sh, to identifie the URL request to the good client
    :param str id_case:             Unique ID creates during the response_handler , to identifie the URL request to the good case.
    :return:                        None
    """

    text = info.split("\n")
    if len(text) == 1:
        text += [".", "", "", "", "", "", "", ""]
    else:
        for _ in range(len(text), 10):
            text += [""]

    if feature != "":
        try:
            print(text[0])
            print(text[1])
            company = get_credentials("company")
            url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Classic_"+company
            headers = {
                        'Content-type': 'application/json', 
                        "Accept-Charset": "UTF-8",
                        'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
                        'jid1': '{0}'.format(jid), 
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
                        'advanced': '{0}'.format(feature)
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
                try:
                    write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                    "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "Yes", "Decision": value}, "fields": {"count": 1}}])
                except UnboundLocalError as error:
                    print(error)
                    sys.exit()
                except Exception as error:
                    print(error)
                pass
            else:
                os.system('logger -t montag -p user.info REST API Timeout')
                info = "No answer received from VNA/Rainbow application - Answer Yes set by default"
                send_message(info, jid)
                value = "1"
        except requests.exceptions.ConnectionError as response:
            print(response)
            value = "1"
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                    "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "Yes"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass
        except requests.exceptions.Timeout as response:
            print("Request Timeout when calling URL: " + url)
            print(response)
            value = "1"
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                    "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "Yes"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass
        except requests.exceptions.TooManyRedirects as response:
            print("Too Many Redirects when calling URL: " + url)
            print(response)
            value = "1"
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                    "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "Yes"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass
        except requests.exceptions.RequestException as response:
            print("Request exception when calling URL: " + url)
            print(response)
            value = "1"
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                    "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "Yes"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass
    else:
        print("feature variable empty")
        sys.exit()
    return value

def send_alert_advanced(subject, action, result, jid):
    """
    This function takes as argument the notification subject, notification action and result. 
    :param str subject:                        Notification subject
    :param str action:                         Preventive Action done
    :param str result:                         Preventive Result
    :param int Card:                           Set to 0 for sending notification without card
    :param int Email:                          0 if email is disabled, 1 if email is enabled
    :return:                                   None
    """
    company = get_credentials("company")
    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Alert_"+company
    headers = {
                'Content-type': 'application/json', 
                "Accept-Charset": "UTF-8",
                'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
                'jid1': '{0}'.format(jid),
                'jid2': '{0}'.format(jid),
                'jid3': '{0}'.format(jid),              
                'subject': '{0}'.format(subject),
                'action': '{0}'.format(action),
                'result': '{0}'.format(result),
                'Card': '0',
                'Email': '0',
                'Advanced': '0'
                }
    print(headers)
    try:
        response = requests.get(url, headers=headers, timeout=0.5)
        code = re.findall(r"<Response \[(.*?)\]>", str(response))
        if "200" in code:
            os.system('logger -t montag -p user.info 200 OK')
            print("Response  Text from VNA")
            value = response.text
            print(value)
            print(code)
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No", "Decision": "Success"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass
        else:
            os.system('logger -t montag -p user.info REST API Timeout')
            pass
    except requests.exceptions.ConnectionError as response:
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
    except requests.exceptions.Timeout as response:
        print("Request Timeout when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
    except requests.exceptions.TooManyRedirects as response:
        print("Too Many Redirects when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
    except requests.exceptions.RequestException as response:
        print("Request exception when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass


def send_file(filename_path, subject, action, result, category, jid):
    """ 
    This function takes as argument the file containins command outputs, the notification subject, notification action and result. 
    This function is called for attaching file on Rainbow or Email notification
    :param str filename_path:                  Path of file attached to the notification
    :param str subject:                        Notification subject
    :param str action:                         Preventive Action done
    :param str result:                         Preventive Result
    :param int Card:                           Set to 0 for sending notification without card
    :param int Email:                          0 if email is disabled, 1 if email is enabled
    :return:                                   None
    """

    company = get_credentials("company")
    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_File_"+company
    request_debug = "Call VNA REST API Method POST path %s" % url
    print(request_debug)
    os.system('logger -t montag -p user.info Call VNA REST API Method POST')
    headers = {
                'Content-type': "text/plain", 
                'Content-Disposition': ("attachment;filename={0}_troubleshooting.log").format(category),
                'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
                'jid1': '{0}'.format(jid),
                'subject': '{0}'.format(subject),
                'action': '{0}'.format(action),
                'result': '{0}'.format(result),
                'Card': '0',
                'Email': '0'}
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
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No", "Decision": "Success"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass
        else:
            os.system('logger -t montag -p user.info REST API Timeout')
            pass
    except requests.exceptions.ConnectionError as response:
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
    except requests.exceptions.Timeout as response:
        print("Request Timeout when calling URL: " + url)
        print(response)
        try:
           write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
    except requests.exceptions.TooManyRedirects as response:
        print("Too Many Redirects when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
    except requests.exceptions.RequestException as response:
        print("Request exception when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass

if __name__ == "__main__":
    switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()
    send_message("text", jid)