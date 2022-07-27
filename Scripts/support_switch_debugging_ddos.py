#!/usr/local/bin/python3.7

import sys
import os
import json
import re
from support_tools_OmniSwitch import get_credentials, debugging, script_has_run_recently
from time import gmtime, strftime, localtime, sleep
from support_send_notification import *
from database_conf import *
import syslog

syslog.openlog('support_switch_debugging_ddos')
syslog.syslog(syslog.LOG_INFO, "Executing script")


runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]

switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

last = ""
with open("/var/log/devices/lastlog_ddos.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_ddos.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_ddos.json", "r", errors='ignore') as log_file:
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
        print("File /var/log/devices/lastlog_ddos.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_ddos.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_ddos.json - Index error in regex")
        exit()

    try:
        ddos_type = re.findall(r"Denial of Service attack detected: <(.*?)>", msg)[0]
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_power_supply_down.json - Index error in regex")
        exit()

    function = "ddos"
    if script_has_run_recently(300,ipadd,function):
        print('you need to wait before you can run this again')
        syslog.syslog(syslog.LOG_INFO, "Executing script exit because executed within 5 minutes time period")
        exit()

notif = "A Denial of Service Attack is detected on OmniSwitch \"" + host + "\" IP: " + ipadd + " of type " + ddos_type
syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
send_message_detailed(notif)
try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "DDOS_Type": ddos_type}, "fields": {"count": 1}}])
    syslog.syslog(syslog.LOG_INFO, "Statistics saved")
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass

# Enable debugging logs for getting IP Attacker's IP Address "swlog appid ipv4 subapp all level debug3"
appid = "ipv4"
subapp = "all"
level = "debug3"
# Call debugging function from support_tools_OmniSwitch
syslog.syslog(syslog.LOG_INFO, "Call debugging function from support_tools_OmniSwitch - swlog appid ipv4 subapp all level debug3")
debugging(switch_user, switch_password, ipadd, appid, subapp, level)
syslog.syslog(syslog.LOG_INFO, "Debugging applied")

# clear lastlog file
open('/var/log/devices/lastlog_ddos.json', 'w').close()

sys.exit(0)
