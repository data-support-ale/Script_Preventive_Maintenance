#!/usr/bin/env python3

from distutils.log import info
import sys
import os
import json
import datetime
from time import strftime, localtime, time, sleep
from support_tools_OmniSwitch import get_credentials, ssh_connectivity_check, get_file_sftp
from support_send_notification import *
from database_conf import *
import re
import time
import syslog

syslog.openlog('support_switch_saa')
syslog.syslog(syslog.LOG_INFO, "   ")
syslog.syslog(syslog.LOG_INFO, "Executing script")
syslog.syslog(syslog.LOG_INFO, "   ")

from pattern import set_rule_pattern, set_portnumber, set_decision, mysql_save


path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

pattern = sys.argv[1]
print(pattern)
set_rule_pattern(pattern)
# info = ("We received following pattern from RSyslog {0}").format(pattern)
# os.system('logger -t montag -p user.info ' + info)

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company = get_credentials()

date = datetime.date.today()
date_hm = datetime.datetime.today()

last = ""
with open("/var/log/devices/lastlog_saa.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_saa.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_saa.json", "r", errors='ignore') as log_file:
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
        print("File /var/log/devices/lastlog_saa.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_saa.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_saa.json - IndexError")
        exit()
    syslog.syslog(syslog.LOG_INFO, "Executing function set_portnumber 0")
    set_portnumber("0")
    if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
        print("Less than 5 min")
        syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
        exit(0)
    
    # Sample log
    # OS6900_VC swlogd saaCmm sm-proto INFO: SPB:SPB-500-e8-e7-32-cc-f3-4f - Iteration packet loss 4/0

    if "Iteration packet loss" and "ZNA_IP_Ping" in msg:
        try:
            pattern = "Iteration packet loss"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            saa_name = re.findall(r"INFO: (.*?) - Iteration packet loss", msg)[0]
            syslog.syslog(syslog.LOG_INFO, "SAA Name: " + saa_name)
            notif = ("Service Assurance Agent - SAA probe {0} configured on OmniSwitch {1} / {2} failed").format(saa_name,ipadd,host)
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Rainbow Notification")
            send_message(notif)
            syslog.syslog(syslog.LOG_INFO, "Notification sent")
            try:
                set_decision(ipadd, "4")
                mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
                syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision") 
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            l_switch_cmd = []
            l_switch_cmd.append("show system; show chassis; show saa statistics history; show arp; show spb isis nodes; show spb isis adjacency; show spb isis bvlans; show spb isis unicast-table; \
            show spb isis spf bvlan 200; show spb isis spf bvlan 300; show spb isis spf bvlan 400; show spb isis spf bvlan 500; show spb isis spf bvlan 600; \
            show service spb; show spb isis services; show service access; show service 2 debug-info; show service 3 debug-info; show service 4 debug-info; \
            show service 5 debug-info; show service 6 debug-info; show service 32000 debug-info; show unp user")

            for switch_cmd in l_switch_cmd:
                syslog.syslog(syslog.LOG_INFO, "   ")
                syslog.syslog(syslog.LOG_INFO, "Collecting CLI logs on OmniSwitch: " + ipadd)
                syslog.syslog(syslog.LOG_INFO, "   ")
                try:
                    output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
                    if output != None:
                        output = str(output)
                        output_decode = bytes(output, "utf-8").decode("unicode_escape")
                        output_decode = output_decode.replace("', '","")
                        output_decode = output_decode.replace("']","")
                        output_decode = output_decode.replace("['","")
                        print(output_decode)                             
                            
                    else:
                        exception = "Timeout"
                        syslog.syslog(syslog.LOG_INFO, "Timeout")
                        notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                        print(info)
                        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                        syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Rainbow Notification")
                        send_message(notif)
                        syslog.syslog(syslog.LOG_INFO, "Notification sent")

                except Exception as exception:
                    print(exception)
                    syslog.syslog(syslog.LOG_INFO, "Command execution failed - exception: " + str(exception))

        except UnboundLocalError as error:
            print(error)
            syslog.syslog(syslog.LOG_INFO, "UnboundLocalError - Notification sent")
            sys.exit()
        except IndexError as error:
            print(error)
            syslog.syslog(syslog.LOG_INFO, "IndexError - exiting script")
            sys.exit()
    else:
        print("no pattern match - exiting script")
        syslog.syslog(syslog.LOG_INFO, "No pattern match - exiting script")
        sys.exit()