#!/usr/bin/env python3

import sys
import os
import re
import json
from support_tools_OmniSwitch import collect_command_output_linkagg, get_credentials, get_file_sftp, port_monitoring, collect_command_output_lldp_port_description, ssh_connectivity_check, get_arp_entry
from time import strftime, localtime, sleep
import datetime
from support_send_notification import *
# from database_conf import *
import requests
import time
import syslog

syslog.openlog('support_switch_linkagg')
syslog.syslog(syslog.LOG_INFO, "Executing script")

from pattern import set_rule_pattern, set_portnumber, set_decision, get_decision, mysql_save

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

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

# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company, room_id = get_credentials()

date = datetime.date.today()
date_hm = datetime.datetime.today()

last = ""
with open("/var/log/devices/lastlog_linkagg.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_linkagg.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_linkagg.json", "r", errors='ignore') as log_file:
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
        print("File /var/log/devices/lastlog_linkagg.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_linkagg.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_linkagg.json - Index error in regex")
        exit()
 
 
    ## Sample Log
    ## OS6860E_VC_Core swlogd linkAggCmm main INFO: Receive agg port leave request: agg: 1, port: 1/1/1(0)
    ## If we did not receive LACP frame within 3 seconds interval above log is generated and port is put Out of Sync within the LinkAgg, if this is Primary port traffic is dropped till Port is Attached again
    if "Aggregate Down" in msg:
        try:
            pattern = "Aggregate Down"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            port, snmp_port_id, agg, link_status, linkagg_status = re.findall(r"Receive agg port leave request:   Aggregate Down, LACP port: (.*?)\((.*?)\) agg: (.*?) link:(.*?) agg_admin:(.*?)", msg)[0]
            print(port)
        except IndexError:
            print("Index error in regex")
            syslog.syslog(syslog.LOG_INFO, "Index error in regex")
            exit()
    if "leave request: agg" in msg:
        try:
            pattern = "leave request: agg"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            agg, port = re.findall(r"Receive agg port leave request: agg: (.*?), port:(.*?)\(", msg)[0]
            print(port)
        except IndexError:
            print("Index error in regex")
            syslog.syslog(syslog.LOG_INFO, "Index error in regex")
            exit()

    set_portnumber(port)
    if alelog.rsyslog_script_timeout(ipadd + port + pattern, time.time()):
        print("Less than 5 min")
        syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
        exit(0)
        
syslog.syslog(syslog.LOG_INFO, "Executing function get_decision")
decision = get_decision(ipadd)

# if save_resp == "0":
if (len(decision) == 0) or (len(decision) == 1 and decision[0] == 'Yes'):
    port_monitoring(switch_user, switch_password, port, ipadd)
    notif = "A LinkAgg Port Leave occurs on OmniSwitch " + host + " port " + port + " LinkAgg " + agg
    syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
    send_message(notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
    syslog.syslog(syslog.LOG_INFO, "Executing script collect_command_output_lldp_port_description")
    lldp_port_description, lldp_mac_address = collect_command_output_lldp_port_description(switch_user, switch_password, port, ipadd)  
    if lldp_port_description == 0:
        syslog.syslog(syslog.LOG_INFO, "No LLDP Port Description collected")
        device_type = answer = 0
        syslog.syslog(syslog.LOG_INFO, "Executing script collect_command_output_linkagg")
        filename_path, subject, action, result, category = collect_command_output_linkagg(switch_user, switch_password, agg, host, ipadd)
        syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
        syslog.syslog(syslog.LOG_INFO, "Action: " + action)
        syslog.syslog(syslog.LOG_INFO, "Result: " + result)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")            
        send_file(filename_path, subject, action, result, category)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        set_decision(ipadd, "4")
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')
    elif "OAW-AP" in str(lldp_port_description):
        syslog.syslog(syslog.LOG_INFO, "LLDP Remote-System is OAW-AP")
        # If LLDP Remote System is Stellar AP we search for IP Address in ARP Table
        syslog.syslog(syslog.LOG_INFO, "Executing script get_arp_entry")
        device_ip = get_arp_entry(switch_user, switch_password, lldp_mac_address, ipadd)
        device_type = "OAW-AP"
        notif = "A LinkAgg Port Leave occurs on OmniSwitch " + host + " port " + port + " LinkAgg " + agg + " - Port Description: " + lldp_port_description + ". Stellar AP " + device_ip + "/" + lldp_mac_address + " is connected to this port, do you want to collect AP logs? The port-monitoring capture of port " + port + " is available on Server " + ip_server + " directory /tftpboot/"
        # If LLDP Remote System is Stellar AP we propose to collect AP Logs
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
        answer = send_message_request(notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        print(answer)      
        set_decision(ipadd, "4")
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif + " Decision: " + answer, exception='')
    
    else:
        syslog.syslog(syslog.LOG_INFO, "LLDP Remote-System is " + lldp_port_description)

        device_type = "Others"
        filename_path, subject, action, result, category = collect_command_output_linkagg(switch_user, switch_password, agg, host, ipadd)
        action = "A LinkAgg Port Leave occurs on OmniSwitch " + host + " port " + port + " LinkAgg " + agg + " - Port Description: " + lldp_port_description + ". The port-monitoring capture of port " + port + " is available on Server " + ip_server + " directory /tftpboot/"
        syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
        syslog.syslog(syslog.LOG_INFO, "Action: " + action)
        syslog.syslog(syslog.LOG_INFO, "Result: " + result)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")            
        send_file(filename_path, subject, action, result, category)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        set_decision(ipadd, "4")
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')
    sleep(2)
    #### Download port monitoring capture ###
    syslog.syslog(syslog.LOG_INFO, "Downloading port monitoring capture")
    filename= '{0}_pmonitor_linkagg.enc'.format(host)
    remoteFilePath = '/flash/pmonitor.enc'
    localFilePath = "/tftpboot/{0}_{1}-{2}_{3}_{4}".format(date,date_hm.hour,date_hm.minute,ipadd,filename)
    try:
        syslog.syslog(syslog.LOG_INFO, "Executing function get_file_sftp") 
        get_file_sftp(switch_user, switch_password, ipadd, remoteFilePath, localFilePath)
    except FileNotFoundError:
        syslog.syslog(syslog.LOG_INFO, "Error: /flash/pmonitor.enc file not found on OmniSwitch")
        print("/flash/pmonitor.enc file not found on OmniSwitch")
        pass
    except:
        pass

    notif = "Preventive Maintenance Application - LinkAgg issue detected on OmniSwitch " + host + ". Do you want to keep being notified? " + ip_server        #send_message(info, jid)
    syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
    answer = send_message_request(notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
    print(answer)
    syslog.syslog(syslog.LOG_INFO, "Executing function set_decision")
    set_decision(ipadd, answer)
    mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif + " Decision: " + answer, exception='')

elif 'No' in decision:
    print("Decision set to never - exit")
    syslog.syslog(syslog.LOG_INFO, "Decision saved to No - script exit")
    sys.exit()

elif 'yes and remember' in [d.lower() for d in decision]:
    answer = '2'
    print("Decision saved to Yes and remember")
    syslog.syslog(syslog.LOG_INFO, "Decision saved to Yes and remember")
    notif = "Preventive Maintenance Application - A LinkAgg Port Leave has been detected on your network from the port {0} on OmniSwitch {1} / {2}.\nDecision saved for this switch/port is set to Always.".format(port, host, ipadd)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
    answer = send_message(notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
else:
    syslog.syslog(syslog.LOG_INFO, "No answer - Decision set to Yes - Script exit - will be called by next occurence")    


if answer == '1':
    syslog.syslog(syslog.LOG_INFO, "Decision set to Yes")
    if device_type == "OAW-AP":
        syslog.syslog(syslog.LOG_INFO, "Device Type is OAW-AP - Collecting Snapshot logs on WLAN Stellar AP")
        cmd = "ssudo tech_support_command 12 " + ip_server
        syslog.syslog(syslog.LOG_INFO, "SSH Session start")
        syslog.syslog(syslog.LOG_INFO, "Command executed: " + cmd)    
        ssh_connectivity_check(login_AP, pass_AP, device_ip, cmd)
        syslog.syslog(syslog.LOG_INFO, "SSH Session end")
        filename_path, subject, action, result, category = collect_command_output_linkagg(switch_user, switch_password, agg, host, ipadd)
        syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
        syslog.syslog(syslog.LOG_INFO, "Action: " + action)
        syslog.syslog(syslog.LOG_INFO, "Result: " + result)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
        send_file(filename_path, subject, action, result, category)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
    else:
        syslog.syslog(syslog.LOG_INFO, "Device Type is not OAW-AP")
        filename_path, subject, action, result, category = collect_command_output_linkagg(switch_user, switch_password, agg, host, ipadd)
        syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
        syslog.syslog(syslog.LOG_INFO, "Action: " + action)
        syslog.syslog(syslog.LOG_INFO, "Result: " + result)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
        send_file(filename_path, subject, action, result, category)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

elif answer == '2':
    filename_path, subject, action, result, category = collect_command_output_linkagg(switch_user, switch_password, agg, host, ipadd)
    syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
    syslog.syslog(syslog.LOG_INFO, "Action: " + action)
    syslog.syslog(syslog.LOG_INFO, "Result: " + result)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
    send_file(filename_path, subject, action, result, category)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

else:
    print("No decision matching - script exit")
    syslog.syslog(syslog.LOG_INFO, "No decision matching - script exit")
    sys.exit()
