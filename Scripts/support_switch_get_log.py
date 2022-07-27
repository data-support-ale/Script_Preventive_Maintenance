#!/usr/local/bin/python3.7

import sys
import os
import json
import datetime
from time import strftime, localtime
from support_tools_OmniSwitch import get_credentials, get_tech_support_sftp, ssh_connectivity_check
from support_send_notification import send_message_detailed
import re
from database_conf import *
import syslog

syslog.openlog('support_switch_get_log')
syslog.syslog(syslog.LOG_INFO, "Executing script")
dir="/opt/ALE_Script"
attachment_path = "/var/log/server/log_attachment"

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]

switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()
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
        l = []
        l.append('/code ')
        l.append(msg)
        message_reason = ''.join(l)
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
if len(sys.argv) > 1:
    pattern = sys.argv[1]
    print(pattern)
    info = ("We received following pattern from RSyslog {0}").format(pattern)
    syslog.syslog(syslog.LOG_INFO, info)


notif = "A Pattern {1} has been detected in switch(IP : {0}) syslogs. We are collecting logs on syslog server".format(ipadd, pattern)
syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
send_message_detailed(notif)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
send_message_detailed(message_reason)
try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Pattern": pattern}, "fields": {"count": 1}}])
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
syslog.syslog(syslog.LOG_INFO, "Tech_support collected")
print("Starting collecting additionnal logs")
syslog.syslog(syslog.LOG_INFO, "Starting collecting additionnal logs")

notif = "A Pattern {1} has been detected in switch(IP : {0}) syslogs. Tech-support eng complete is collected and stored in /tftpboot/ on server IP Address: {2}".format(ipadd, pattern, ip_server)
syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
send_message_detailed(notif)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

##########################Get More LOGS########################################
text = "More logs about the switch : {0} \n\n\n".format(ipadd)

l_switch_cmd = []
l_switch_cmd.append("show interfaces")
l_switch_cmd.append("show system")
l_switch_cmd.append("show date")
l_switch_cmd.append("show unp user")
print(ipadd)
for switch_cmd in l_switch_cmd:
    cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user, ipadd, switch_cmd)
    syslog.syslog(syslog.LOG_INFO, "Command executed on OmniSwitch: " + cmd)
    try:
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
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
            send_message_detailed(notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                    "Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass 
    except FileNotFoundError as exception:
        notif = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message_detailed(notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                "Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass 

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


notif = "Additional logs collected from switch(IP : {0}) syslogs. and stored in " + attachment_path + " on server IP Address: {2}".format(ipadd, pattern, ip_server)
syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
send_message_detailed(notif)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

open('/var/log/devices/get_log_switch.json', 'w').close()
