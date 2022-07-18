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
import traceback
import syslog

syslog.openlog('support_send_notification')

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
dir="/opt/ALE_Script"
vna_url = "https://vna.preprod.omniaccess-stellar-asset-tracking.com/"

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
    url = vna_url + "/api/flows/NBDNotif_Classic_"+company
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
                'Card': '0',
                'Email': '1',
               }
    syslog.syslog(syslog.LOG_INFO, "URL: " + url)
    syslog.syslog(syslog.LOG_INFO, "Headers: " + str(headers))
    try:
        syslog.syslog(syslog.LOG_INFO, "Calling VNA API - send_message - method GET")
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
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No", "Decision": "Success"}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            except UnboundLocalError as error:
                print(str(error))
                sys.exit()
            except Exception as error:
                print(str(error))
                pass
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
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            except UnboundLocalError as error:
                print(str(error))
                sys.exit()
            except Exception as error:
                print(str(error))
                pass
            pass
    except requests.exceptions.ConnectionError as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Connection Error - " + str(response))
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
            pass
    except requests.exceptions.Timeout as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Timeout - " + str(response))
        print("Request Timeout when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
            pass
    except requests.exceptions.TooManyRedirects as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: TooManyRedirects - " + str(response))
        print("Too Many Redirects when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
            pass
    except requests.exceptions.RequestException as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: " + str(response))
        print("Request exception when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
            pass

def send_test(info, jid,company):
    """ 
    API for testing VNA and Rainbow reachability

    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :return:                        None
    """
    url = vna_url + "/api/flows/NBDNotif_Test_"+company
    headers = {
                'Content-type': 'application/json', 
                "Accept-Charset": "UTF-8",
                'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
                'jid1': '{0}'.format(jid), 
                'info': '{0}'.format(info), 
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
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No", "Decision": "Success"}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            except UnboundLocalError as error:
                print(str(error))
                sys.exit()
            except Exception as error:
                print(str(error))
                pass
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
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            except UnboundLocalError as error:
                print(str(error))
                sys.exit()
            except Exception as error:
                print(str(error))
                pass
            pass
    except requests.exceptions.ConnectionError as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Connection Error - " + str(response))
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
            pass
    except requests.exceptions.Timeout as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Timeout - " + str(response))
        print("Request Timeout when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
            pass
    except requests.exceptions.TooManyRedirects as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: TooManyRedirects - " + str(response))
        print("Too Many Redirects when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
            pass
    except requests.exceptions.RequestException as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: " + str(response))
        print("Request exception when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
            pass

def send_alert(info, jid):
    """
    Send the message in info to a Rainbowbot. This bot will send this message to the jid in parameters

    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :return:                        None
    """
    company = get_credentials("company")
    url = vna_url + "/api/flows/NBDNotif_Alert_"+company
    headers = {
                'Content-type': 'application/json',
                "Accept-Charset": "UTF-8",
                'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
                'jid1': '{0}'.format(jid), 
                'subject': '{0}'.format(info), 
                'Card': '0'
                }
    syslog.syslog(syslog.LOG_INFO, "URL: " + url)
    syslog.syslog(syslog.LOG_INFO, "Headers: " + str(headers))
    try:
        syslog.syslog(syslog.LOG_INFO, "Calling VNA API - send_alert - method GET")
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
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No", "Decision": "Success"}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            except UnboundLocalError as error:
                print(str(error))
                sys.exit()
            except Exception as error:
                print(str(error))
                pass
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
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            except UnboundLocalError as error:
                print(str(error))
                sys.exit()
            except Exception as error:
                print(str(error))
                pass
            pass
    except requests.exceptions.ConnectionError as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Connection Error - " + str(response))
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
            pass
    except requests.exceptions.Timeout as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Timeout - " + str(response))
        print("Request Timeout when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
            pass
    except requests.exceptions.TooManyRedirects as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: TooManyRedirects - " + str(response))
        print("Too Many Redirects when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
            pass
    except requests.exceptions.RequestException as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: " + str(response))
        print("Request exception when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
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
        url = vna_url + "/api/flows/NBDNotif_Classic_"+company
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
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "Yes", "Decision": value}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            except UnboundLocalError as error:
                print(str(error))
                sys.exit()
            except Exception as error:
                print(str(error))
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
            send_message(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            syslog.syslog(syslog.LOG_INFO, "Value set to 1")
            value = "1"
    except requests.exceptions.ConnectionError as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Connection Error - " + str(response))
        print(response)
        syslog.syslog(syslog.LOG_INFO, "Value set to 1")
        value = "1"
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "Yes"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
            pass
    except requests.exceptions.Timeout as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Timeout - " + str(response))
        print(response)
        syslog.syslog(syslog.LOG_INFO, "Value set to 1")
        value = "1"
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "Yes"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
            pass
    except requests.exceptions.TooManyRedirects as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: TooManyRedirects - " + str(response))
        print(response)
        syslog.syslog(syslog.LOG_INFO, "Value set to 1")
        value = "1"
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "Yes"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
            pass
    except requests.exceptions.RequestException as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: " + str(response))
        print(response)
        syslog.syslog(syslog.LOG_INFO, "Value set to 1")
        value = "1"
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "Yes"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
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
        syslog.syslog(syslog.LOG_INFO, "Rainbow Adaptive Card with 4th option: " + feature)
        try:
            print(text[0])
            print(text[1])
            company = get_credentials("company")
            url = vna_url + "/api/flows/NBDNotif_Classic_"+company
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
                try:
                    write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "Yes", "Decision": value}, "fields": {"count": 1}}])
                    syslog.syslog(syslog.LOG_INFO, "Statistics saved")
                except UnboundLocalError as error:
                    print(str(error))
                    sys.exit()
                except Exception as error:
                    print(str(error))
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
                send_message(notif, jid)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
                syslog.syslog(syslog.LOG_INFO, "Value set to 1")
                value = "1"
        except requests.exceptions.ConnectionError as response:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Connection Error - " + str(response))
            print(response)
            syslog.syslog(syslog.LOG_INFO, "Value set to 1")
            value = "1"
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "Yes"}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            except UnboundLocalError as error:
                print(str(error))
                sys.exit()
            except Exception as error:
                print(str(error))
                pass
        except requests.exceptions.Timeout as response:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Timeout - " + str(response))
            print(response)
            syslog.syslog(syslog.LOG_INFO, "Value set to 1")
            value = "1"
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "Yes"}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            except UnboundLocalError as error:
                print(str(error))
                sys.exit()
            except Exception as error:
                print(str(error))
                pass
        except requests.exceptions.TooManyRedirects as response:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: TooManyRedirects - " + str(response))
            print(response)
            syslog.syslog(syslog.LOG_INFO, "Value set to 1")
            value = "1"
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "Yes"}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            except UnboundLocalError as error:
                print(str(error))
                sys.exit()
            except Exception as error:
                print(str(error))
                pass
        except requests.exceptions.RequestException as response:
            syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: " + str(response))
            print(response)
            syslog.syslog(syslog.LOG_INFO, "Value set to 1")
            value = "1"
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "Yes"}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            except UnboundLocalError as error:
                print(str(error))
                sys.exit()
            except Exception as error:
                print(str(error))
                pass
    else:
        print("feature variable empty")
        syslog.syslog(syslog.LOG_INFO, "Feature variable is empty - script exit")
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
    url = vna_url + "/api/flows/NBDNotif_Alert_"+company
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
                'Email': '1',
                'Advanced': '0'
                }
    print(headers)
    try:
        syslog.syslog(syslog.LOG_INFO, "URL: " + url)
        syslog.syslog(syslog.LOG_INFO, "Headers: " + str(headers))
        print("Sending request")
        syslog.syslog(syslog.LOG_INFO, "Calling VNA API - send_alert_advanced - method GET")
    
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
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No", "Decision": "Success"}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            except UnboundLocalError as error:
                print(str(error))
                sys.exit()
            except Exception as error:
                print(str(error))
                pass
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
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            except UnboundLocalError as error:
                print(str(error))
                sys.exit()
            except Exception as error:
                print(str(error))
                pass
            pass
    except requests.exceptions.ConnectionError as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Connection Error - " + str(response))
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
            pass
    except requests.exceptions.Timeout as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Timeout - " + str(response))
        print("Request Timeout when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
            pass
    except requests.exceptions.TooManyRedirects as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: TooManyRedirects - " + str(response))
        print("Too Many Redirects when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
            pass
    except requests.exceptions.RequestException as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: " + str(response))
        print("Request exception when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
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
    url = vna_url + "/api/flows/NBDNotif_File_"+company
    request_debug = "Call VNA REST API Method POST path %s" % url
    print(request_debug)
    headers = {
                'Content-type': "text/plain", 
                'Content-Disposition': ("attachment;filename={0}_troubleshooting.log").format(category),
                'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
                'jid1': '{0}'.format(jid),
                'subject': '{0}'.format(subject),
                'action': '{0}'.format(action),
                'result': '{0}'.format(result),
                'Card': '0',
                'Email': '1'}
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
        syslog.syslog(syslog.LOG_INFO, "Calling VNA API - send_file - method GET")
    
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
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No", "Decision": "Success"}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            except UnboundLocalError as error:
                print(str(error))
                sys.exit()
            except Exception as error:
                print(str(error))
                pass
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
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            except UnboundLocalError as error:
                print(str(error))
                sys.exit()
            except Exception as error:
                print(str(error))
                pass
            pass

    except requests.exceptions.ConnectionError as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Connection Error - " + str(response))
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
            pass
    except requests.exceptions.Timeout as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: Timeout - " + str(response))
        print("Request Timeout when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
            pass
    except requests.exceptions.TooManyRedirects as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: TooManyRedirects - " + str(response))
        print("Too Many Redirects when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
            pass
    except requests.exceptions.RequestException as response:
        syslog.syslog(syslog.LOG_INFO, "VNA API Call exception: " + str(response))
        print("Request exception when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(str(error))
            sys.exit()
        except Exception as error:
            print(str(error))
            pass

if __name__ == "__main__":
    try:
        switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()
        company = "Ubuntu_lab_2_1_11"
        room_id = "room_ceab1e350d6c40418bf232f3056550e5@muc.openrainbow.com"
        info = "Celui qui a une maison n en a qu une  celui qui n en a aucune en a mille.\nCelui qui regarde longtemps les songes devient semblable a son ombre.\nLe silence est la parure de l ignorant dans l assemblee des sages. \nUnie à l ocean  la goutte d eau demeure."
        send_message(info, jid)
        info = "Le vélo est le moyen de transport le plus démocratique. Le vélo est le plus audacieux, stimulant car il donne à son propriétaire le sentiment tentant de liberté, c'est pourquoi on peut dire sans aucune exagération, le vélo est un symbole de liberté."
        send_test(info, jid,company)
        send_message_request("Test card.\nDo you want a coffee?", jid)
        feature = "Reboot dans le doute"
        send_message_request_advanced("Test advanced card.\nDid you plug the Ethernet cable?", jid, feature)
        info = "Alerte canicule en Bretagne!"
        send_alert(info, jid)
        filename_path = ""
        subject = "Preventive Maintenance application - Ceci est un test"
        action = "Aucun resultat n est attendu"
        result = "Ni auncune action"
        category = "test"
        send_file(filename_path, subject, action, result, category, jid)
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