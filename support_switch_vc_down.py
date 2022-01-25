#!/usr/bin/env python

import sys
import os
import getopt
import json
import logging
import datetime
from time import gmtime, strftime, localtime,sleep
from support_tools import get_credentials,get_server_log_ip,get_jid,extract_ip_port,get_mail,send_python_file_sftp,get_file_sftp
from support_send_notification import send_message,send_file,send_mail
import subprocess
from database_conf import *

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

switch_user, switch_password, jid, gmail_user, gmail_password, mails,ip_server_log = get_credentials()
ip_switch,nb_vc = extract_ip_port("vc_down")



if jid !='':
         info = "Log of device : {0}".format(ip_switch)
         send_file(info,jid,ip_switch)
         info = "A default on VC unity {} from device {} has been detected".format(nb_vc,ip_switch)
         send_message(info,jid)


open('/var/log/devices/lastlog_vc_down.json','w').close()

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ip_switch, "VC_Unit": nb_vc}, "fields": {"count": 1}}])
except UnboundLocalError as error:
    print(error)
    sys.exit()