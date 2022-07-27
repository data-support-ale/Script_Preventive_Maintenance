#!/usr/bin/env python3

import sys
import os
import re
import json
from support_tools_OmniSwitch import get_credentials
from time import strftime, localtime, sleep
from support_send_notification import *
# from database_conf import *
import time

from pattern import set_rule_pattern, set_portnumber, set_decision, get_decision, mysql_save

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)

pattern = sys.argv[1]
print(pattern)
set_rule_pattern(pattern)
# info = ("We received following pattern from RSyslog {0}").format(pattern)
# os.system('logger -t montag -p user.info ' + info)

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company, room_id = get_credentials()

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

    port, reason = re.findall(
        r"Port (.*?) in violation - source (.*?) reason", msg)[0]

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


# always 1
#never -1
# ? 0
set_portnumber(port)
decision = get_decision(ip)
if alelog.rsyslog_script_timeout(ip + port + pattern, time.time()):
    print("Less than 5 min")
    os.system('logger -t montag -p user.info Executing script ' + script_name + ' less than 5 minutes')
    exit(0)
# save_resp = check_save(ip, port, "violation")

# if save_resp == "0":
if (len(decision) == 0) or (len(decision) == 1 and decision[0] == 'Yes'):
    notif = "A port violation occurs on OmniSwitch " + nom + "port " + port + \
        ", source: " + reason + ". Do you want to clear the violation? " + ip_server
    # answer = send_message_request(notif, jid)
    answer =  send_message_request_detailed(notif, jid1, jid2, jid3)

    set_decision(ip, answer)

    print(answer)
    # if answer == "2":
    #     add_new_save(ip, port, "violation", choice="always")
    # elif answer == "0":
    #     add_new_save(ip, port, "violation", choice="never")
# elif save_resp == "-1":
elif 'No' in decision:
    sys.exit()
# elif save_resp == "1":
elif 'yes and remember' in [d.lower() for d in decision]:
    answer = '2'
else:
    answer = '1'

if answer == '1':
    os.system('logger -t montag -p user.info Process terminated')
    # CLEAR VIOLATION
    cmd = "clear violation port " + port
    os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
        switch_password, switch_user, ip, cmd))
    # if jid1 != '' or jid2 != '' or jid3 != '':
    #     info = "Log of device : {0}".format(ip)
    #     # send_file(info, jid, ip)
    #     info = "A port violation has been cleared up on device {}".format(ip)
    #     # send_message_detailed(info, jid1, jid2, jid3)
    #     send_message_detailed(info, jid1, jid2, jid3)

    sleep(2)
    filename_path = "/var/log/devices/" + nom + "/syslog.log"
    category = "port_violation"
    subject = "A port violation is detected:".format(nom, ip)
    action = "Violation on OmniSwitch {0}, port {1} has been cleared up".format(nom, port)
    result = "Find enclosed to this notification the log collection"
#    support_tools_OmniSwitch.send_file(filename_path, subject, action, result, category)
    send_file_detailed(subject, jid1, action, result, company, filename_path)
    mysql_save(runtime=_runtime, ip_address=ip, result='success', reason=action, exception='')

elif answer == '2':
    os.system('logger -t montag -p user.info Process terminated')
    # CLEAR VIOLATION
    cmd = "clear violation port " + port
    os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
        switch_password, switch_user, ip, cmd))

    mysql_save(runtime=_runtime, ip_address=ip, result='success', reason=cmd, exception='')

else:
    set_decision(ip, "0")
    print("Mail request set as no")
    mysql_save(runtime=_runtime, ip_address=ip, result='success', reason="Mail request set as no", exception='')
    
    os.system('logger -t montag -p user.info Mail request set as no')
    sleep(1)
