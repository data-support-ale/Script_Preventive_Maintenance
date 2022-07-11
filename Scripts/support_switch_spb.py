#!/usr/local/bin/python3.7

import sys
import os
import re
import json
from support_tools_OmniSwitch import get_credentials, collect_command_output_spb
from time import strftime, localtime, sleep
from support_send_notification import *
from database_conf import *
import re
import syslog

syslog.openlog('support_switch_spb')
syslog.syslog(syslog.LOG_INFO, "Executing script")


runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

# Log sample
#{"@timestamp":"2022-01-11T14:30:23+01:00","type":"syslog_json","relayip":"10.130.7.245","hostname":"os6900_vc_core","message":"<134>Jan 11 14:30:23 OS6900_VC_Core swlogd isis_spb_0 ADJACENCY INFO: Lost L1 adjacency with e8e7.32f5.b58b on ifId 1013","end_msg":""}

last = ""
with open("/var/log/devices/lastlog_spb.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_spb.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_spb.json", "r", errors='ignore') as log_file:
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
        print("File /var/log/devices/lastlog_spb.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_spb.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_spb.json - JSONDecodeError")
        exit()

    try:
        adjacency_id, port_1 = re.findall(r"Lost L1 adjacency with (.*?) on ifId (.*)", msg)[0]
        syslog.syslog(syslog.LOG_INFO, "Adjacency Identifier: " + adjacency_id + " - Port from syslog: " + port_1)
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_spb.json - JSONDecodeError")
        exit()
    # n=int(port_1)
    n = len(str(port_1))
    print(n)
    dig = []
    dig = list(int(port_1) for port_1 in str(port_1))
    if n < 6:
        dig_1 = [1, 0]
        dig = dig_1 + dig
    unit = dig[0]
    slot = dig[2]
    port = str(dig[4]) + str(dig[5])

    port = str(unit) + "/" + str(slot) + "/" + str(port)
    port = "Port " + port
    if n > 6:
        if str(dig[6]) != "0":
            port = str(dig[6]) + str(dig[7])
            port = "Linkagg " + port
        else:
            port = str(dig[7])
            port = "Linkagg " + port
    print(port)
    syslog.syslog(syslog.LOG_INFO, "Port: " + port)

#notif = ("Preventive Maintenance Application - SPB Adjacency state change on OmniSwitch {0} / {1}.\n\nDetails:\n- System ID : {2}\n- Port : {3}\nPlease check the SPB Adjacent node connectivity.").format(host,ipadd,adjacency_id,port)
filename_path, subject, action, result, category = collect_command_output_spb(switch_user, switch_password, host, ipadd, adjacency_id, port)
syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
syslog.syslog(syslog.LOG_INFO, "Action: " + action)
syslog.syslog(syslog.LOG_INFO, "Result: " + result)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")            
send_file(filename_path, subject, action, result, category, jid)
syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

sleep(1)
open('/var/log/devices/lastlog_spb.json', 'w').close()

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"System_ID": adjacency_id, "IP": ipadd, "Port/LinkAgg": port}, "fields": {"count": 1}}])
    syslog.syslog(syslog.LOG_INFO, "Statistics saved")
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass 
