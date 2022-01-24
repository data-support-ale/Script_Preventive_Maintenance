#!/usr/bin/env python

import sys
import os
import getopt
import json
import logging
import subprocess
from time import gmtime, strftime, localtime
from support_tools import get_credentials_ap,get_server_log_ip,get_jid,extract_ip_port,get_mail
from support_send_notification import send_message, send_mail_loop,send_file,send_mail

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'



runtime = strftime("%d_%b_%Y_%H_%M_%S_0000", localtime())
uname = os.system('uname -a')
system_name = os.uname()[1].replace(" ", "_")
logging.info("Running on {0} at {1} ".format(system_name, runtime))

ip_server_log = get_server_log_ip()

ip_ap,port=extract_ip_port("get_log_ap")
user_ap,password_ap,technical_support_code = get_credentials_ap()
jid = get_jid()
mail_user,mail_password,mails = get_mail()
#get the paswd with the technical support code
cmd = "sshpass -p {0} ssh -v -o StrictHostKeyChecking=no {1}@{2} genrpd {3}".format(password_ap,user_ap,ip_ap,technical_support_code)
run=cmd.split()
p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
out, err = p.communicate()
pass_root = out.decode('ascii').strip()
#send snapshot to log server
print(pass_root)
cmd = "/usr/sbin/take_snapshot.sh start {}".format(ip_server_log)
os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  root@{1} {2}".format(pass_root, ip_ap, cmd))
logging.info(bcolors.OKGREEN + runtime + ': upload starting' + bcolors.ENDC)


logging.info(bcolors.OKGREEN + 'Process finished!' + bcolors.ENDC)


info = "A Pattern has been detected in AP(IP : {0}) syslogs. A snapshot has been sent at the server logs : {1}, in the directory : /tftpboot/ ".format(ip_ap,ip_server_log)
if jid !='':
   send_message(info,jid)
   send_file(info,jid,ip_ap)


if mail_user !='':
   subject= "A Pattern has been detected in AP logs"
   send_mail(ip_ap,"0",info,subject,mail_user,mail_password,mails)


#clear log file
open('/var/log/devices/get_log_ap.json','w').close()


