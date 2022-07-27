#!/usr/bin/env python3

import sys
import os
import json
import datetime
from time import strftime, localtime
import syslog
from support_tools_OmniSwitch import get_credentials, get_tech_support_sftp, ssh_connectivity_check
from support_send_notification import *
import subprocess
import re
# from database_conf import *
import time

from pattern import set_rule_pattern, set_portnumber, set_decision, mysql_save

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.notif Executing script ' + script_name)

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
date = datetime.date.today()
date_hm = datetime.datetime.today()

path = os.path.dirname(__file__)

switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company, room_id = get_credentials()
filename = 'tech_support_complete.tar'

last = ""
with open("/var/log/devices/get_log_switch.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/get_log_switch.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/get_log_switch.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/get_log_switch.json empty")
        exit()

pattern = ""
if len(sys.argv) > 2:
    pattern = sys.argv[1]
    print(pattern)
    notif = ("We received following pattern from RSyslog {0}").format(pattern)
    os.system('logger -t montag -p user.notif ' + notif)
    _pattern = sys.argv[2]
elif len(sys.argv) > 1:
    _pattern = sys.argv[1]

print(_pattern)
set_rule_pattern(_pattern)
# notif = ("We received following pattern from RSyslog {0}").format(_pattern)
# os.system('logger -t montag -p user.notif ' + notif)


def get_port():
    with open("/var/log/devices/get_log_switch.json", "r", errors='ignore') as log_file:
        try:
            log_json = json.load(log_file)
            ipadd = log_json["relayip"]
            host = log_json["hostname"]
            msg = log_json["message"]
        except json.decoder.JSONDecodeError:
            print("File /var/log/devices/get_log_switch.json empty")
            exit()
        port = 0
        return port

set_portnumber(get_port())
set_decision(ipadd, "4")
if alelog.rsyslog_script_timeout(ipadd + str(get_port()) + _pattern, time.time()):
    print("Less than 5 min")
    exit(0)


notif = "A Pattern {1} has been detected in switch(IP : {0}) syslogs. We are collecting logs on syslog server".format(ipadd, pattern)
syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
send_message(notif)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
set_decision(ipadd, "4")
try:
    mysql_save(runtime=runtime, ip_address=ipadd, result='success', reason=notif, exception='')
    syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision")    
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass   


### TECH-SUPPORT ENG COMPLETE ###
get_tech_support_sftp(switch_user, switch_password, host, ipadd)

print("Starting collecting additionnal logs")

notif = "A Pattern {1} has been detected in switch(IP : {0}) syslogs. Tech-support eng complete is collected and stored in /tftpboot/ on syslog server".format(ipadd, pattern)
syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
send_message(notif)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
set_decision(ipadd, "4")
try:
    mysql_save(runtime=runtime, ip_address=ipadd, result='success', reason=notif, exception='')
    syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision")    
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass   


##########################Get More LOGS########################################
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
text = "More logs about the switch : {0} \n\n\n".format(ipadd)

l_switch_cmd = []
l_switch_cmd.append("show interfaces")
l_switch_cmd.append("show system")
l_switch_cmd.append("show date")
l_switch_cmd.append("show unp user")
print(ipadd)
for switch_cmd in l_switch_cmd:
    cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
        switch_password, switch_user, ipadd, switch_cmd)
    try:
        output = ssh_connectivity_check(
            switch_user, switch_password, ipadd, switch_cmd)
        output = subprocess.check_output(
            cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
        if output != None:
            output = output.decode('UTF-8').strip()
            text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output)
        else:
            exception = "Timeout"
            notif = (
                "Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
            print(notif)
            _notif = notif + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.notif ' + notif)
            send_message(notif)
            try:
                mysql_save(runtime=_runtime, ip_address=ipadd, result='failure', reason=_notif , exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
    except subprocess.TimeoutExpired as exception:
        notif = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(notif)
        _notif = notif + ' ; ' + 'command executed - {0}'.format(switch_cmd)
        os.system('logger -t montag -p user.notif ' + notif)
        send_message(notif)
        try:
            mysql_save(runtime=_runtime, ip_address=ipadd, result='failure', reason=_notif , exception=exception)
        except UnboundLocalError as error:
            print(error)
        sys.exit()
    except FileNotFoundError as exception:
        notif = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(notif)
        _notif = notif + ' ; ' + 'command executed - {0}'.format(switch_cmd)
        os.system('logger -t montag -p user.notif ' + notif)
        send_message(notif)
        try:
            mysql_save(runtime=_runtime, ip_address=ipadd, result='failure', reason=_notif , exception=exception)
        except UnboundLocalError as error:
            print(error)
        sys.exit()

mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason="More logs about the switch : {0} \n\n\n".format(ipadd), exception='')
date = datetime.date.today()
date_hm = datetime.datetime.today()

filename = "{0}_{1}-{2}_{3}_logs".format(date,
                                         date_hm.hour, date_hm.minute, ipadd)
f_logs = open(path + '/{0}.txt'.format(filename), 'w', errors='ignore')
f_logs.write(text)
f_logs.close()
###############################################################################

#### Send file with additionnal logs #####
filename = path + '/{0}.txt'.format(filename)
print(filename)


notif = "Additional logs collected from switch(IP : {0}) syslogs. and stored in {3} on server IP Address: {2}".format(ipadd, pattern, ip_server, path)
syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
send_message(notif)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
set_decision(ipadd, "4")
try:
    mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
    syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision")    
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass   


open('/var/log/devices/get_log_switch.json', 'w').close()
