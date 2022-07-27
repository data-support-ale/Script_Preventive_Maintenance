#!/usr/bin/env python3

import sys
import os
import json
from time import strftime, localtime
from support_tools_OmniSwitch import get_credentials
from support_send_notification import *
from database_conf import *
import re
import syslog
import time
syslog.openlog('support_server_monitoring')
syslog.syslog(syslog.LOG_INFO, "Executing script")

from pattern import set_rule_pattern, set_portnumber, set_decision, mysql_save

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

# Script init
script_name = sys.argv[0]

pattern = sys.argv[1]
print(pattern)
set_rule_pattern(pattern)
# info = ("We received following pattern from RSyslog {0}").format(pattern)
# os.system('logger -t montag -p user.info ' + info)

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company = get_credentials()

last = ""
with open("/var/log/devices/lastlog_server_monitoring.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_server_monitoring.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_server_monitoring.json", "r", errors='ignore') as log_file:
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
        print("File /var/log/devices/lastlog_server_monitoring.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_server_monitoring.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_server_monitoring.json - IndexError")
        exit()

# always 1
#never -1
# ? 0

# Sample log if TFTP Service does not start
# systemd[1]: Failed to start LSB: HPA's tftp server.
# systemd[1790]: Failed to start Notification regarding a crash report.
# systemd[1]: Failed to start Rotate log files.
if "Failed to start LSB" in msg:
    try:
        set_decision(ipadd, "4")
        pattern = "TFTP Service issue"
        syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
        notif = ("Preventive Maintenance Application - TFTP Service issue detected on Preventive Maintenance server {0}.\nThis service is used for log collection of WLAN Stellar AP. Do you want to restart the TFTP Service?").format(ip_server)        
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
        answer = send_message_request(notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
            syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision")    
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass   
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except IndexError as error:
        print(error)
        sys.exit()
    sys.exit()
    # Sample log
    # qqchose
# Sample log for authentication failure
# {"@timestamp":"2022-07-01T13:12:07.633156+02:00","type":"syslog_json","relayip":"127.0.0.1","hostname":"debian2","message":"<38>Jul  1 13:12:07 sshd[48692]: Failed password for admin-support from 10.130.7.174 port 33196 ssh2","end_msg":""}
elif "Failed password" in msg:
    try:
        set_decision(ipadd, "4")
        pattern = "SSH Authentication issue"
        login,user_ip,port,service = re.findall(r"Failed password for (.*?) from (.*?) port (.*?) (.*)", msg)[0]
        syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
        notif = ("Preventive Maintenance Application - SSH Authentication failure when connecting to Preventive Maintenance server {0} .\n\nDetails: \n- User: {1}\n- IP Address: {2}\n- Protocol: {3}").format(ip_server,login,user_ip,service)      
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Notification")
        send_message(notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
            syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision")    
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass  
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except IndexError as error:
        print(error)
        sys.exit()
    sys.exit()

# Sample log for SSH Disconnection
# {"@timestamp":"2022-07-19T17:28:56.584953+02:00","type":"syslog_json","relayip":"127.0.0.1","hostname":"debian2","message":"<38>Jul 19 17:28:56 sshd[16814]: Disconnecting authenticating user admin-support 10.61.34.9 port 42274: Too many authentication failures [preauth]","end_msg":""}
elif "Disconnecting authenticating user" in msg:
    try:
        set_decision(ipadd, "4")
        pattern = "Disconnecting authenticating user"
        login,user_ip,port = re.findall(r"Disconnecting authenticating user (.*?) (.*?) port (.*?): Too many authentication failures", msg)[0]
        syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
        notif = ("Preventive Maintenance Application - SSH Authentication failure when connecting to Preventive Maintenance server {0} .\n\nDetails: \n- User: {1}\n- IP Address: {2}.").format(ip_server,login,user_ip)      
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Notification")
        send_message(notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
            syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision")    
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass  
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except IndexError as error:
        print(error)
        sys.exit()
    sys.exit()

# Log if Disk issue
elif "No space left on device" in msg:
    try:
        set_decision(ipadd, "4")
        pattern = "No space left on device"
        syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
        notif = ("Preventive Maintenance Application - No space left on device issue detected on Preventive Maintenance server {0}").format(ip_server)      
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Notification")
        send_message(notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
            syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision")    
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass  
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except IndexError as error:
        print(error)
        sys.exit()
    sys.exit()
else:
    try:
        set_decision(ipadd, "4")
        service_issue_reason = re.findall(r"Failed to start (.*)", msg)[0]
        notif = ("Preventive Maintenance Application - Service failure detected on Preventive Maintenance server {0} .\n\nDetails: \n- Reason: {1}").format(ip_server,service_issue_reason)      
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send Notification")
        send_message(notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
            syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision")    
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass 
    except UnboundLocalError as error:
        print(error)
        syslog.syslog(syslog.LOG_INFO, "Regex does not match")
        sys.exit()
    except IndexError as error:
        print(error)
        syslog.syslog(syslog.LOG_INFO, "Regex does not match")
        sys.exit()
    sys.exit()
