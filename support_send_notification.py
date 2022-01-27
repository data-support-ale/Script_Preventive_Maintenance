#!/usr/bin/env python
import sys
import os
import getopt
import json
import logging
import subprocess
import requests
from time import gmtime, strftime, localtime, sleep
import smtplib
#from support_tools import save_attachment
import mimetypes
import re
from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from support_web_receiver_class import Receiver,start_web
from database_conf import *

def send_message(info,jid):
    """ 
    Send the message in info to a Rainbowbot. This bot will send this message to the jid in parameters

    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :return:                        None
    """


    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Classic_EMEA"
    headers = {'Content-type': 'application/json', "Accept-Charset": "UTF-8", 'jid1': '{0}'.format(jid), 'toto': '{0}'.format(info),'Card': '0'}
    response = requests.get(url, headers=headers)
    try:
        write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()

def send_alert(info,jid):
    """
    Send the message in info to a Rainbowbot. This bot will send this message to the jid in parameters

    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :return:                        None
    """


    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Alert_EMEA"
    headers = {'Content-type': 'application/json', "Accept-Charset": "UTF-8", 'jid1': '{0}'.format(jid), 'toto': '{0}'.format(info),'Card': '0'}
    response = requests.get(url, headers=headers)
    try:
        write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()

def send_message_aijaz(subject,info,jid):
    """
    Send the message in info to a Rainbowbot. This bot will send this message to the jid in parameters

    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :return:                        None
    """


    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Aijaz"
    headers = {'Content-type': 'application/json', "Accept-Charset": "UTF-8", 'jid1': '{0}'.format(jid), 'tata': '{0}'.format(subject),'toto': '{0}'.format(info), 'Card': '0'}
    response = requests.get(url, headers=headers)
    try:
        write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()

def send_message_request(info,jid,receiver):
    """ 
    Send the message, with a URL requests  to a Rainbowbot. This bot will send this message and request to the jid in parameters

    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :param str ip_server:           IP Adress of the server log , which is also a web server
    :param str id_client:           Unique ID creates during the Setup.sh, to identifie the URL request to the good client
    :param str id_case:             Unique ID creates during the response_handler , to identifie the URL request to the good case.
    :return:                        None
    """

    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Classic_EMEA"
    headers = {'Content-type': 'application/json', "Accept-Charset": "UTF-8",'Card': '1', 'jid1': '{0}'.format(jid), 'toto': '{0}.'.format(info)}
    response = requests.get(url, headers=headers)
    print(response)
    try:
        write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "Yes"}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    print(response.text)
    receiver.set_answer(response.text)
    sleep(1)
    url = "http://127.0.0.1:5200/?id=rainbow"
    try:
        response = requests.get(url)
        print(response)
    except requests.exceptions.ConnectionError:
        print("Max retries exceeded when calling URL: " + url)
        sys.exit()
    except requests.exceptions.Timeout:
        print("Request Timeout when calling URL: " + url)
        sys.exit()    
    except requests.exceptions.TooManyRedirects:
        print("Too Many Redirects when calling URL: " + url)
        sys.exit()    
    except requests.exceptions.RequestException:
        print("Request exception when calling URL: " + url)
        sys.exit()      

def send_file(info,jid,ipadd,filename_path =''):
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

    if not filename_path =='':
       payload=open("{0}".format(filename_path),'rb')
       filename = filename_path.split("/")
       filename = filename[-1]
       info = "Log of device : {0}".format(ipadd)
       url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_File_EMEA"
       headers = {  'Content-type':"application/x-tar",'Content-Disposition': "attachment;filename={0}".format(filename), 'jid1': '{0}'.format(jid),'toto': '{0}'.format(info)}
       #files = {'file': fp}
       response = requests.post(url, headers=headers, data=payload)
       print(response)
       try:
           write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response}, "fields": {"count": 1}}])
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
            hour, min, sec = re.findall(r"\d?\d (\d\d):(\d\d):(\d\d)", timestamp)[0]
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
                new_hour, new_min, new_sec = re.findall(r"\d?\d (\d\d):(\d\d):(\d\d)", str(timestamp))[0]
                new_file += line
                if int(new_hour) >= int(hour) and int(new_min) >= int(min) and int(new_sec) >= int(sec):
                    break
    
    with open("/var/log/devices/short_attachment.log", "w+", errors='ignore') as s_log:
        print(new_file)
        s_log.write(new_file)



    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_File_EMEA"
    headers = {  'Content-type':"text/plain",'Content-Disposition': "attachment;filename=short_attachment.log", 'jid1': '{0}'.format(jid),'toto': '{0}'.format(info)}
    files = {'file': open('/var/log/devices/short_attachment.log','r')}
    response = requests.post(url,files=files, headers=headers)
    try:
        write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    sleep(5)
