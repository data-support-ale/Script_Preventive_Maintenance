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
import syslog

syslog.openlog('support_switch_get_log')
syslog.syslog(syslog.LOG_INFO, "Executing script")
from pattern import set_rule_pattern, set_portnumber, set_decision, mysql_save
attachment_path = "/var/log/server/log_attachment"
path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.notif Executing script ' + script_name)

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
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
        print(msg)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog IP Address: " + ipadd)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog Hostname: " + host)
        #syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + msg)
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_power_supply_down.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/get_log_switch.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/get_log_switch.json - Index error in regex")
        exit()

pattern = ""
if len(sys.argv) > 2:
    pattern = sys.argv[1]
    print(pattern)
    notif = ("We received following pattern from RSyslog {0}").format(pattern)
    syslog.syslog(syslog.LOG_INFO, notif)
    _pattern = sys.argv[2]
elif len(sys.argv) > 1:
    _pattern = sys.argv[1]

print(_pattern)
set_rule_pattern(_pattern)


set_portnumber("0")
set_decision(ipadd, "4")
if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
    syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
    exit(0)



notif = "A Pattern {1} has been detected in switch(IP : {0}) syslogs. We are collecting logs on syslog server".format(ipadd, pattern)
syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Sending notification")
send_message(notif)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
try:
    set_decision(ipadd, "4")
    mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
    syslog.syslog(syslog.LOG_INFO, "Statistics saved")
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass 

### TECH-SUPPORT ENG COMPLETE ###
syslog.syslog(syslog.LOG_INFO, "Executing function get_tech_support_sftp")
get_tech_support_sftp(switch_user, switch_password, host, ipadd)
mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason="Tech-Support file collected", exception='')
syslog.syslog(syslog.LOG_INFO, "Statistics saved")
syslog.syslog(syslog.LOG_INFO, "Tech_support collected")
print("Starting collecting additionnal logs")
syslog.syslog(syslog.LOG_INFO, "Starting collecting additionnal logs")
##########################Get More LOGS########################################
text = "More logs about the switch : {0} \n\n\n".format(ipadd)

l_switch_cmd = []
l_switch_cmd.append("show interfaces; show system; show chassis; show date; show unp user")
print(ipadd)
for switch_cmd in l_switch_cmd:
    output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
    if output != None:
        output = str(output)
        output_decode = bytes(output, "utf-8").decode("unicode_escape")
        output_decode = output_decode.replace("', '","")
        output_decode = output_decode.replace("']","")
        output_decode = output_decode.replace("['","")
        text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output_decode)
    else:
        exception = "Timeout"
        notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
        _info = notif + ' ; ' + 'command executed - {0}'.format(switch_cmd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message(notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            set_decision(ipadd, "4")
            mysql_save(runtime=runtime, ip_address=ipadd,result='failure', reason=_info, exception=exception)
        except UnboundLocalError as exception:
            print(exception)
        except Exception as exception:
            print(exception)
        os._exit(1)

date = datetime.date.today()
date_hm = datetime.datetime.today()
syslog.syslog(syslog.LOG_INFO, "Additionnal logs collected")

filename = "{0}_{1}-{2}_{3}_logs".format(date,
                                         date_hm.hour, date_hm.minute, ipadd)
f_logs = open(attachment_path + '/{0}.txt'.format(filename), 'w', errors='ignore')
f_logs.write(text)
f_logs.close()
syslog.syslog(syslog.LOG_INFO, "Logs path: " + attachment_path + filename)
###############################################################################

#### Send file with additionnal logs #####
filename = attachment_path + '/{0}.txt'.format(filename)
print(filename)


notif = "Tech-Support file and additional logs collected from switch(IP : {0}) syslogs. and stored in " + attachment_path + " on server IP Address: {2}".format(ipadd, pattern, ip_server)
syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
send_message(notif)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
open('/var/log/devices/get_log_switch.json', 'w').close()
