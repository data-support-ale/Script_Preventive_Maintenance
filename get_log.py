#!/usr/bin/env python

import sys
import os
import getopt
import json
import logging
from time import gmtime, strftime, localtime
from support_tools import get_credentials_ap,get_server_log_ip,get_jid,extract_ip_port,get_mail
from support_send_notification import send_message, send_mail_loop,send_file,send_mail
import subprocess

logging.basicConfig(filename='/home/azmaso/debug.log', filemode='w', level=logging.DEBUG)

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
uname = os.system('uname -a')
system_name = os.uname()[1].replace(" ", "_")
logging.info("Running on {0} at {1} ".format(system_name, runtime))

#email account properties

#switch credentials and command to launch script
user = "admin"
#host = "192.168.0.253"
#cmd = "python /flash/python/get_logs_usb_key.py"


switch_user, switch_password, jid, gmail_user, gmail_password, mails,ip_server_log = get_credentials()
ip_switch,port = extract_ip_port("get_log_switch")




def collect_log_usb()
    #ssh session to start python script remotely
     cmd = "python /flash/python/get_logs_usb_key.py"
     logging.info(runtime + ': upload starting')
     os.system("sshpass -p 'Letacla01*' ssh -v {0}@{1} {2}".format(user, ip_host, cmd))
     logging.info(runtime + ' Process finished!')


def collect_log_sftp()
    #ssh session to start python script remotely
     cmd = "python /flash/python/def collect_log_usb()
    #ssh session to start python script remotely
     cmd = "python /flash/python/get_logs_sftp.py"
     logging.info(runtime + ': upload starting')
     os.system("sshpass -p 'Letacla01*' ssh -v {0}@{1} {2}".format(user, ip_host, cmd))
     logging.info(runtime + ' Process finished!')


