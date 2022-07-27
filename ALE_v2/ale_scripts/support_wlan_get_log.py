#!/usr/bin/env python3

import sys
import os
import getopt
import re
import json
import logging
import subprocess
from time import gmtime, strftime, localtime
from support_tools_OmniSwitch import get_credentials
from support_send_notification import *
import time

from pattern import set_rule_pattern, set_portnumber, set_decision, mysql_save

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

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

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)

pattern = sys.argv[1]
print(pattern)
set_rule_pattern(pattern)
# info = ("We received following pattern from RSyslog {0}").format(pattern)
# os.system('logger -t montag -p user.info ' + info)

_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

runtime = strftime("%d_%b_%Y_%H_%M_%S_0000", localtime())
uname = os.system('uname -a')
system_name = os.uname()[1].replace(" ", "_")
logging.info("Running on {0} at {1} ".format(system_name, runtime))

switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company, room_id = get_credentials()
last = ""
with open("/var/log/devices/get_log_ap.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/get_log_ap.json", "w", errors='ignore') as log_file:
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

set_portnumber("0")
set_decision(ip, "4")
if alelog.rsyslog_script_timeout(ip + "0" + pattern, time.time()):
    print("Less than 5 min")
    exit(0)

# get the paswd with the technical support code
cmd = "sshpass -p {0} ssh -v -o StrictHostKeyChecking=no {1}@{2} genrpd {3}".format(
    pass_AP, login_AP, ip, tech_pass)
run = cmd.split()
p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
out, err = p.communicate()
pass_root = out.decode('ascii').strip()
# send snapshot to log server
print(pass_root)
cmd = "/usr/sbin/take_snapshot.sh start {}".format(ip_server)
os.system(
    "sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  root@{1} {2}".format(pass_root, ip, cmd))
logging.info(bcolors.OKGREEN + runtime + ': upload starting' + bcolors.ENDC)


logging.info(bcolors.OKGREEN + 'Process finished!' + bcolors.ENDC)


info = "A Pattern has been detected in AP(IP : {0}) syslogs. A snapshot has been sent at the server logs : {1}, in the directory : /tftpboot/ ".format(
    ip, ip_server)
if jid1 != '' or jid2 != '' or jid3 != '':
    mysql_save(runtime=_runtime, ip_address=ip, result='success', reason=info, exception='')
    # send_message_detailed(info, jid1, jid2, jid3)
    # send_file(info, jid, ip)
    send_message_detailed(info, jid1, jid2, jid3)
    #send_file_detailed(info, jid1, 'Additionnal rules - LAN', 'Status: File sent', company, filename_path)


# clear log file
open('/var/log/devices/get_log_ap.json', 'w').close()
