#!/usr/bin/env python

import sys
import os
import re
import json
from support_tools_OmniSwitch import get_credentials
from time import strftime, localtime, sleep
from support_send_notification import send_message, send_file, send_message_request
from database_conf import *
from support_tools_OmniSwitch import add_new_save, check_save

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user,switch_password,mails,jid,ip_server,login_AP,pass_AP,tech_pass,random_id,company = get_credentials()

last = ""
with open("/var/log/devices/lastlog_violation.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_violation.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_violation.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ip = log_json["relayip"]
        nom = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_violation.json empty")
        exit()

    port, reason = re.findall(r"Port (.*?) in violation - source (.*?) reason", msg)[0]

    if reason == "0":
        reason = "Unknown"
    elif reason == "1":
        reason = "Access Guardian"
    elif reason == "2":
        reason = "QOS Policy"
    elif reason == "3":
        reason = "Net Sec"
    elif reason == "4":
        reason = "UDLD"
    elif reason == "5":
        reason = "NI supervision (Fabric Stability)"
    elif reason == "6":
        reason = "OAM"
    elif reason == "8":
        reason = "LFP"
    elif reason == "9":
        reason = "Link monitoring"
    elif reason == "10":
        reason = "LBD"
    elif reason == "11":
        reason = "SPB"
    elif reason == "12":
        reason = "ESM"
    elif reason == "13":
        reason = "ESM"
    elif reason == "14":
        reason = "LLDP"


#always 1 
#never -1
#? 0
save_resp = check_save(ip,port,"violation")

if save_resp == "0":
    notif = "A port violation occurs on OmniSwitch " + nom + "port " + port + ", source: " + reason + ". Do you want to clear the violation? " + ip_server 
    answer = send_message_request(notif,jid)
    print(answer)
    if answer == "2":
        add_new_save(ip,port,"violation",choice = "always")
    elif answer == "0":
        add_new_save(ip,port,"violation",choice = "never")
elif save_resp == "-1":
    sys.exit()
else:
    answer = '1'

if answer == '1':
    os.system('logger -t montag -p user.info Process terminated')
    # CLEAR VIOLATION
    cmd = "clear violation port " + port
    os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user, ip,cmd))
    if jid != '':
        info = "Log of device : {0}".format(ip)
        send_file(info, jid, ip)
        info = "A port violation has been cleared up on device {}".format(ip)
        send_message(info, jid)
        
elif answer == '2':
    os.system('logger -t montag -p user.info Process terminated')
    # CLEAR VIOLATION
    cmd = "clear violation port " + port
    os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user, ip,cmd))

else:
    print("Mail request set as no")
    os.system('logger -t montag -p user.info Mail request set as no')
    sleep(1)

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ip, "Reason": reason, "port" : port}, "fields": {"count": 1}}])
except UnboundLocalError as error:
    print(error)
    sys.exit()