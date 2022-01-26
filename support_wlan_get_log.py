#!/usr/bin/env python

import sys
import os
import getopt
import re
import json
import logging
import subprocess
from time import gmtime, strftime, localtime
from support_tools_OmniSwitch import get_credentials
from support_send_notification import send_message, send_file

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

switch_user,switch_password,mails,jid,ip_server,login_AP,pass_AP,tech_pass,random_id,company = get_credentials()
last = ""
with open("/var/log/devices/get_log_ap.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/get_log_ap.json","w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/get_log_ap.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ip = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("/var/log/devices/get_log_ap.json empty")
        exit()
        
#get the paswd with the technical support code
cmd = "sshpass -p {0} ssh -v -o StrictHostKeyChecking=no {1}@{2} genrpd {3}".format(pass_AP,login_AP,ip,tech_pass)
run=cmd.split()
p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
out, err = p.communicate()
pass_root = out.decode('ascii').strip()
#send snapshot to log server
print(pass_root)
cmd = "/usr/sbin/take_snapshot.sh start {}".format(ip_server)
os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  root@{1} {2}".format(pass_root, ip, cmd))
logging.info(bcolors.OKGREEN + runtime + ': upload starting' + bcolors.ENDC)


logging.info(bcolors.OKGREEN + 'Process finished!' + bcolors.ENDC)


info = "A Pattern has been detected in AP(IP : {0}) syslogs. A snapshot has been sent at the server logs : {1}, in the directory : /tftpboot/ ".format(ip,ip_server)
if jid !='':
   send_message(info,jid)
   send_file(info,jid,ip)



#clear log file
open('/var/log/devices/get_log_ap.json','w').close()


