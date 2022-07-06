#!/usr/local/bin/python3.7

import sys
import os
import re
import json
from support_tools_OmniSwitch import collect_command_output_linkagg, get_credentials, send_file, script_has_run_recently, get_file_sftp, port_monitoring, collect_command_output_lldp_port_description, ssh_connectivity_check, get_arp_entry
from time import strftime, localtime, sleep
import datetime
from support_send_notification import send_message_request, send_message, send_message_request_advanced
from database_conf import *
from support_tools_OmniSwitch import add_new_save, check_save
import requests
import syslog

syslog.openlog('support_switch_linkagg')
syslog.syslog(syslog.LOG_INFO, "Executing script")


runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

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
        syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + msg)
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
        
# always 1
#never -1
# ? 0
syslog.syslog(syslog.LOG_INFO, "Executing function check_save")
save_resp = check_save(ipadd, agg, "linkagg")

function = "linkagg"
if script_has_run_recently(300,ipadd,function):
    print('you need to wait before you can run this again')
    syslog.syslog(syslog.LOG_INFO, "Executing script exit because executed within 5 minutes time period")
    exit()


if save_resp == "0":
    port_monitoring(switch_user, switch_password, port, ipadd)
    notif = ("Preventive Maintenance Application - A LinkAgg Port Leave occurs on OmniSwitch {0} / {1}.\nPort: {2}\nLinkAgg: {3}").format(host,ipadd,port,agg)
    syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
    send_message(notif, jid)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
    syslog.syslog(syslog.LOG_INFO, "Executing script collect_command_output_lldp_port_description")
    lldp_port_description, lldp_mac_address = collect_command_output_lldp_port_description(switch_user, switch_password, port, ipadd)  
    if lldp_port_description == 0:
        device_type = answer = 0
        syslog.syslog(syslog.LOG_INFO, "No LLDP Port Description collected")
        syslog.syslog(syslog.LOG_INFO, "Executing script collect_command_output_linkagg")
        filename_path, subject, action, result, category = collect_command_output_linkagg(switch_user, switch_password, agg, host, ipadd)
        syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
        syslog.syslog(syslog.LOG_INFO, "Action: " + action)
        syslog.syslog(syslog.LOG_INFO, "Result: " + result)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")            
        send_file(filename_path, subject, action, result, category, jid)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

    elif "OAW-AP" in str(lldp_port_description):
        syslog.syslog(syslog.LOG_INFO, "LLDP Remote-System is OAW-AP")
        # If LLDP Remote System is Stellar AP we search for IP Address in ARP Table
        syslog.syslog(syslog.LOG_INFO, "Executing script get_arp_entry")
        device_ip = get_arp_entry(switch_user, switch_password, lldp_mac_address, ipadd)
        device_type = "OAW-AP"
        notif = ("Preventive Maintenance Application - A LinkAgg Port Leave occurs on OmniSwitch {0} / {1}.Port: {2} - LinkAgg: {3} - Port Description: {4}\nWLAN Stellar AP: {5} / {6} is connected to this port. Do you want to collect AP logs? The port-monitoring capture of port {7} is available on Server {8} directory /tftpboot/").format(host,ipadd,port,agg,lldp_port_description,device_ip,lldp_mac_address,port,ip_server)
#        notif = "Preventive Maintenance Application - A LinkAgg Port Leave occurs on OmniSwitch " + host + " port " + port + " LinkAgg " + agg + " - Port Description: " + lldp_port_description + ". WLAN Stellar AP " + device_ip + "/" + lldp_mac_address + " is connected to this port, do you want to collect AP logs? The port-monitoring capture of port " + port + " is available on Server " + ip_server + " directory /tftpboot/"
        # If LLDP Remote System is Stellar AP we propose to collect AP Logs
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
        answer = send_message_request(notif, jid)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        print(answer)      
    else:
        device_type = "Others"
        syslog.syslog(syslog.LOG_INFO, "LLDP Remote-System is " + lldp_port_description)
        answer = 0
        filename_path, subject, action, result, category = collect_command_output_linkagg(switch_user, switch_password, agg, host, ipadd)
#        action = "Preventive Maintenance Application - A LinkAgg Port Leave occurs on OmniSwitch " + host + " port " + port + " LinkAgg " + agg + " - Port Description: " + lldp_port_description + ". The port-monitoring capture of port " + port + " is available on Server " + ip_server + " directory /tftpboot/"
        action = ("Preventive Maintenance Application - A LinkAgg Port Leave occurs on OmniSwitch {0} / {1}.Port: {2} - LinkAgg: {3} - Port Description: {4}. The port-monitoring capture of port {5} is available on Server {6} directory /tftpboot/").format(host,ipadd,port,agg,lldp_port_description,port,ip_server)
        syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
        syslog.syslog(syslog.LOG_INFO, "Action: " + action)
        syslog.syslog(syslog.LOG_INFO, "Result: " + result)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")            
        send_file(filename_path, subject, action, result, category, jid)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
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
    if answer == "2":
        add_new_save(ipadd,port, "linkagg", choice="always")
        syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Port: " + port + " Choice: " + " Always")

    elif answer == "0":
        add_new_save(ipadd,port, "linkagg", choice="never")
        syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Port: " + port + " Choice: " + " Never")
    else:
        pass

    notif = ("Preventive Maintenance Application - LinkAgg issue detected on OmniSwitch {0} / {1}.\nDo you want to keep being notified? ").format(host,ipadd)        #send_message(info, jid)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
    answer = send_message_request(notif, jid)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

    print(answer)
    if answer == "2":
        add_new_save(ipadd, agg, "linkagg", choice="always")
        syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Agg: " + agg + " Choice: " + " Always")
    elif answer == "0":
        add_new_save(ipadd, agg, "linkagg", choice="never")
        syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Agg: " + agg + " Choice: " + " Never")

    syslog.syslog(syslog.LOG_INFO, "Rainbow Acaptive Card answer: " + answer)

elif save_resp == "-1":
    print("Decision saved to No - script exit")
    syslog.syslog(syslog.LOG_INFO, "Decision saved to No - script exit")
    sys.exit()

elif save_resp == "1":
    answer = '2'
    print("Decision saved to Yes and remember")
    syslog.syslog(syslog.LOG_INFO, "Decision saved to Yes and remember")
    notif = "Preventive Maintenance Application - A LinkAgg Port Leave has been detected on your network from the port {0} on OmniSwitch {1} / {2}.\nDecision saved for this switch/port is set to Always.".format(port, host, ipadd)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
    answer = send_message(notif, jid)
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
        send_file(filename_path, subject, action, result, category, jid)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
    else:
        syslog.syslog(syslog.LOG_INFO, "Device Type is not OAW-AP")
        filename_path, subject, action, result, category = collect_command_output_linkagg(switch_user, switch_password, agg, host, ipadd)
        syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
        syslog.syslog(syslog.LOG_INFO, "Action: " + action)
        syslog.syslog(syslog.LOG_INFO, "Result: " + result)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
        send_file(filename_path, subject, action, result, category, jid)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

elif answer == '2':
    filename_path, subject, action, result, category = collect_command_output_linkagg(switch_user, switch_password, agg, host, ipadd)
    syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
    syslog.syslog(syslog.LOG_INFO, "Action: " + action)
    syslog.syslog(syslog.LOG_INFO, "Result: " + result)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
    send_file(filename_path, subject, action, result, category, jid)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

else:
    print("No decision matching - script exit")
    syslog.syslog(syslog.LOG_INFO, "No decision matching - script exit")
    sys.exit()