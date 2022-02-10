#!/usr/local/bin/python3.7
from cProfile import run
import sys
import requests
from time import sleep, strftime, localtime
import re
from database_conf import *
from support_tools_OmniSwitch import get_credentials


runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())


def send_message(info, jid):
    """ 
    Send the message in info to a Rainbowbot. This bot will send this message to the jid in parameters

    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :return:                        None
    """
    company = get_credentials("company")
    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Classic_" + company
    headers = {'Content-type': 'application/json', "Accept-Charset": "UTF-8",
               'jid1': '{0}'.format(jid), 'toto': '{0}'.format(info), 'Card': '0'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        code = re.findall(r"<Response \[(.*?)\]>", str(response))
        if "200" in code:
            os.system('logger -t montag -p user.info 200 OK')
            print("Response  Text from VNA")
            value = response.text
            print(value)
            print(code)
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No", "Decision": value}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
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
    except requests.exceptions.Timeout as response:
        print("Request Timeout when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
    except requests.exceptions.TooManyRedirects as response:
        print("Too Many Redirects when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
    except requests.exceptions.RequestException as response:
        print("Request exception when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()


def send_alert(info, jid):
    """
    Send the message in info to a Rainbowbot. This bot will send this message to the jid in parameters

    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :return:                        None
    """
    company = get_credentials("company")
    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Alert_"+company
    headers = {'Content-type': 'application/json', "Accept-Charset": "UTF-8",
               'jid1': '{0}'.format(jid), 'toto': '{0}'.format(info), 'Card': '0'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        code = re.findall(r"<Response \[(.*?)\]>", str(response))
        if "200" in code:
            os.system('logger -t montag -p user.info 200 OK')
            print("Response  Text from VNA")
            value = response.text
            print(value)
            print(code)
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No", "Decision": value}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
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
    except requests.exceptions.Timeout as response:
        print("Request Timeout when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
    except requests.exceptions.TooManyRedirects as response:
        print("Too Many Redirects when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
    except requests.exceptions.RequestException as response:
        print("Request exception when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()


def send_message_aijaz(subject, info, jid):
    """
    Send the message in info to a Rainbowbot. This bot will send this message to the jid in parameters

    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :return:                        None
    """

    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Aijaz"
    headers = {'Content-type': 'application/json', "Accept-Charset": "UTF-8",
               'jid1': '{0}'.format(jid), 'tata': '{0}'.format(subject), 'toto': '{0}'.format(info), 'Card': '0'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        code = re.findall(r"<Response \[(.*?)\]>", str(response))
        if "200" in code:
            os.system('logger -t montag -p user.info 200 OK')
            print("Response  Text from VNA")
            value = response.text
            print(value)
            print(code)
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No", "Decision": value}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
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
    except requests.exceptions.Timeout as response:
        print("Request Timeout when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
    except requests.exceptions.TooManyRedirects as response:
        print("Too Many Redirects when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
    except requests.exceptions.RequestException as response:
        print("Request exception when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()


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
    try:
        company = get_credentials("company")
        url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Classic_"+company
        headers = {'Content-type': 'application/json', "Accept-Charset": "UTF-8",
                   'Card': '1', 'jid1': '{0}'.format(jid), 'toto': '{0}.'.format(info)}
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
    return value


def send_file(info, jid, ipadd, filename_path=''):
    """ 
    Send the attachement to a Rainbowbot. This bot will send this file to the jid in parameters
    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :param str ipadd:               IP Address of the device concerned by the issue 
    :return:                        None
    """


#    if re.search("A Pattern has been detected in switch",info) :
#       cmd = "ls -t /tftpboot/"
#       run=cmd.split()
#       p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
#       p = subprocess.Popen(('grep',ipadd),stdin=p.stdout, stdout=subprocess.PIPE)
#       p =  subprocess.Popen(('head','-n','1'),stdin=p.stdout,stdout=subprocess.PIPE)
#       out, err = p.communicate()
#       out=out.decode('UTF-8').strip()

#       fp = open("/tftpboot/{0}".format(out),'rb')
#       info = "Log of device : {0}".format(ipadd)
#       url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotifFile/"
#       headers = { 'Content-Transfer-Encoding': 'application/gzip', 'jid1': '{0}'.format(jid),'toto': '{0}'.format(info)}
#       files = {'file': open('/tftpboot/{0}'.format(out),'rb')}
#       params = {'filename'  :'{0}'.format(out)}
#       response = requests.post(url,files=files,params=params, headers=headers)

    if not filename_path == '':
        payload = open("{0}".format(filename_path), 'rb')
        filename = filename_path.split("/")
        filename = filename[-1]
        info = "Log of device : {0}".format(ipadd)
        company = get_credentials("company")
        url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_File_"+company
        headers = {'Content-type': "application/x-tar", 'Content-Disposition': "attachment;filename={0}".format(
            filename), 'jid1': '{0}'.format(jid), 'toto': '{0}'.format(info)}
        #files = {'file': fp}

        try:
            response = requests.post(url, headers=headers,
                                     data=payload, timeout=120)
            code = re.findall(r"<Response \[(.*?)\]>", str(response))
            if "200" in code:
                os.system('logger -t montag -p user.info 200 OK')
                print("Response  Text from VNA")
                value = response.text
                print(value)
                print(code)
                try:
                    write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                    "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No", "Decision": value}, "fields": {"count": 1}}])
                except UnboundLocalError as error:
                    print(error)
                    sys.exit()
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
        except requests.exceptions.Timeout as response:
            print("Request Timeout when calling URL: " + url)
            print(response)
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                    "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
        except requests.exceptions.TooManyRedirects as response:
            print("Too Many Redirects when calling URL: " + url)
            print(response)
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                    "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
        except requests.exceptions.RequestException as response:
            print("Request exception when calling URL: " + url)
            print(response)
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                    "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()

    info = "Log of device : {0}".format(ipadd)

    with open("/var/log/devices/attachment.log", "r+", errors='ignore') as log_file:
        for line in log_file:
            timestamp = ""
            if re.search(r"\d?\d \d\d:\d\d:\d\d", line):
                timestamp = re.findall(r"\d?\d \d\d:\d\d:\d\d", line)[0]
                break
        if re.search(r"\d?\d (\d\d):(\d\d):(\d\d)", timestamp):
            hour, min, sec = re.findall(
                r"\d?\d (\d\d):(\d\d):(\d\d)", timestamp)[0]
            sec = int(sec) + 80
            if sec > 60:
                min = int(min) + 1
                sec -= 60
        else:
            hour, min, sec = (24, 59, 59)

        new_file = ""
        for line in log_file:
            if re.search(r"\d?\d \d\d:\d\d:\d\d", line):
                timestamp = re.findall(r"\d?\d \d\d:\d\d:\d\d", line)[0]
                new_hour, new_min, new_sec = re.findall(
                    r"\d?\d (\d\d):(\d\d):(\d\d)", str(timestamp))[0]
                new_file += line
                if int(new_hour) >= int(hour) and int(new_min) >= int(min) and int(new_sec) >= int(sec):
                    break

    with open("/var/log/devices/short_attachment.log", "w+", errors='ignore') as s_log:
        print(new_file)
        s_log.write(new_file)
    company = get_credentials("company")
    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_File_"+company
    headers = {'Content-type': "text/plain", 'Content-Disposition': "attachment;filename=short_attachment.log",
               'jid1': '{0}'.format(jid), 'toto': '{0}'.format(info)}
    files = {'file': open('/var/log/devices/short_attachment.log', 'r')}
    response = requests.post(url, files=files, headers=headers, timeout=120)
    try:
        response = requests.post(
            url, files=files, headers=headers, timeout=120)
        code = re.findall(r"<Response \[(.*?)\]>", str(response))
        if "200" in code:
            os.system('logger -t montag -p user.info 200 OK')
            print("Response  Text from VNA")
            value = response.text
            print(value)
            print(code)
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No", "Decision": value}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
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
    except requests.exceptions.Timeout as response:
        print("Request Timeout when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
    except requests.exceptions.TooManyRedirects as response:
        print("Too Many Redirects when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
    except requests.exceptions.RequestException as response:
        print("Request exception when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
    sleep(5)
