#!/usr/local/bin/python3.7

import os
import json
import logging
import sys
from time import gmtime, strftime, localtime
from support_tools_Stellar import get_credentials, collect_logs
from support_send_notification import send_message, send_file


runtime = strftime("%d_%b_%Y_%H_%M_%S_0000", localtime())
uname = os.system('uname -a')
system_name = os.uname()[1].replace(" ", "_")
logging.info("Running on {0} at {1} ".format(system_name, runtime))

pattern = sys.argv[1]
print(pattern)

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()
last = ""
with open("/var/log/devices/get_log_ap.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/get_log_ap.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/get_log_ap.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("/var/log/devices/get_log_ap.json empty")
        exit()

# get the paswd with the technical support code
#cmd = "sshpass -p {0} ssh -v -o StrictHostKeyChecking=no {1}@{2} genrpd {3}".format(pass_AP, login_AP, ip, tech_pass)
#run = cmd.split()
#p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
#out, err = p.communicate()
#pass_root = out.decode('ascii').strip()
# Collect snapshot and additionnal logs
#cmd = "/usr/sbin/take_snapshot.sh start {}".format(ip_server)

filename_path, subject, action, result, category = collect_logs(login_AP, pass_AP, ipadd, pattern)
send_file(filename_path, subject, action, result, category, jid)

# clear log file
open('/var/log/devices/get_log_ap.json', 'w').close()