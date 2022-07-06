#!/usr/local/bin/python3.7

import sys
import os
import getopt
import json
import logging
import subprocess
from time import gmtime, strftime, localtime, sleep
import requests
import datetime
#import smtplib
#import mimetypes
import re
from support_tools_OmniSwitch import get_credentials, get_tech_support_sftp, get_pmd_file_sftp, send_file
from support_send_notification import send_message, send_alert
#import pysftp
from database_conf import *
import syslog

syslog.openlog('support_switch_core_dump')
syslog.syslog(syslog.LOG_INFO, "Executing script")


runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

# Example of JSON content
#### {"@timestamp":"2021-11-10T09:42:02.867257+01:00","type":"syslog_json","relayip":"10.130.7.244","hostname":"OS6860N","message":"10:55:46.686 OS6860E-Core2 swlogd COREDUMPER  ALRM: Dumping core for task dpcmm","end_msg":""}
### {"@timestamp":"2021-11-10T09:42:02.867257+01:00","type":"syslog_json","relayip":"10.130.7.244","hostname":"OS6860N","message":"OS6860E-Core2 swlogd PMD main ALRT: PMD generated at /flash/pmd/pmd-agCmm-12.29.2020-11.26.28","end_msg":""}

# Variables
filename = 'tech_support_complete.tar'
filename_pmd = '/flash/pmd/pmd-xx'
appid = "unknown"

# Function called when Core Dump is observed
def pmd_issue(ipadd, jid):
    info = "Preventive Maintenance Application - A Core DUMP is generated by OmniSwitch {0} / {1}".format(host,ipadd)
    syslog.syslog(syslog.LOG_INFO, info)
    #send_alert(info, jid)
    try:
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd}, "fields": {"count": 1}}])
        syslog.syslog(syslog.LOG_INFO, "Statistics saved")
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 


def extract_ipadd():
    last = ""
    with open("/var/log/devices/lastlog_pmd.json", "r", errors='ignore') as log_file:
        for line in log_file:
            last = line

    with open("/var/log/devices/lastlog_pmd.json", "w", errors='ignore') as log_file:
        log_file.write(last)

    with open("/var/log/devices/lastlog_pmd.json", "r", errors='ignore') as log_file:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        ipadd = str(ipadd)
        message_reason = log_json["message"]
        syslog.syslog(syslog.LOG_DEBUG, "Syslog IP Address: " + ipadd)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog Hostname: " + host)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + message_reason)
        l = []
        l.append('/code ')
        l.append(message_reason)
        message_reason = ''.join(l)
        print(ipadd)
    return ipadd, host, message_reason


def extract_pmd_path():
    last = ""
    with open("/var/log/devices/lastlog_pmd.json", "r", errors='ignore') as log_file:
        for line in log_file:
            last = line

    with open("/var/log/devices/lastlog_pmd.json", "w", errors='ignore') as log_file:
        log_file.write(last)

    with open("/var/log/devices/lastlog_pmd.json", "r", errors='ignore') as log_file:
        try:
            log_json = json.load(log_file)
            ipadd = log_json["relayip"]
            host = log_json["hostname"]
            message_reason = log_json["message"]
            syslog.syslog(syslog.LOG_DEBUG, "Syslog IP Address: " + ipadd)
            syslog.syslog(syslog.LOG_DEBUG, "Syslog Hostname: " + host)
            syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + message_reason)
            l = []
            l.append('/code ')
            l.append(message_reason)
            message_reason = ''.join(l)
            print(ipadd)
        except json.decoder.JSONDecodeError:
            print("File /var/log/devices/lastlog_pmd.json empty")
            syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_pmd.json - JSONDecodeError")
            exit()
        except IndexError:
            print("Index error in regex")
            syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_pmd.json - Index error in regex")
            exit()
        try:    
            filename_pmd = re.findall(r"PMD generated at (.*)", message_reason)[0]
            if "flash" in filename_pmd:
                appid = re.findall(r"pmd-(.*)-",filename_pmd)[0]
                pattern = r'[0-9]'
                appid = re.sub(pattern, '', appid)
                appid = appid.replace('-..',"",2)
                print(appid)
            print(filename_pmd)
        except IndexError:
            print("Index error in regex when extracting appid")
            syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_pmd.json - Index error in regex when extracting appid")
            exit()
    return filename_pmd, message_reason, appid

print("Core DUMP - call function collecting log")
syslog.syslog(syslog.LOG_INFO, "Executing function extract_ipadd")
ipadd, host, message_reason = extract_ipadd()

### Notification Rainbow ###
syslog.syslog(syslog.LOG_INFO, "Executing function pmd_issue")
pmd_issue(ipadd, jid)

### TECH-SUPPORT ENG COMPLETE ###
syslog.syslog(syslog.LOG_INFO, "Executing function get_tech_support_sftp")
get_tech_support_sftp(switch_user, switch_password, host, ipadd)

### get PMD FILE ###
print("Starting collecting PMD file")
syslog.syslog(syslog.LOG_INFO, "Executing function extract_pmd_path")
filename_pmd, message_reason, appid = extract_pmd_path()
syslog.syslog(syslog.LOG_INFO, "Executing function get_pmd_file_sftp")
filename_path = get_pmd_file_sftp(switch_user, switch_password, ipadd, filename_pmd)
print(filename_path)

if jid != '':
    notif = ("Preventive Maintenance Application - A Core DUMP is generated by OmniSwitch {0} / {1} on function {2}.\nTech-support eng complete and PMD files are collected and stored in server.\nPlease contact ALE Customer Support team.").format(host, ipadd, appid)
    syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
    send_message(notif, jid)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

    try:
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Task": appid}, "fields": {"count": 1}}])
        syslog.syslog(syslog.LOG_INFO, "Statistics saved")
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 

sys.exit(0)
