#!/usr/local/bin/python3.7

from ipaddress import ip_address
import sys
import os
import re
import json
from support_tools_OmniSwitch import get_credentials, collect_command_output_storm, send_file, script_has_run_recently, get_file_sftp, port_monitoring, ssh_connectivity_check
from time import strftime, localtime, sleep
import datetime
from support_send_notification import send_message_request, send_message
from database_conf import *
from support_tools_OmniSwitch import add_new_save, check_save
import syslog

syslog.openlog('support_switch_storm')
syslog.syslog(syslog.LOG_INFO, "Executing script")


runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

date = datetime.date.today()
date_hm = datetime.datetime.today()

last = ""
with open("/var/log/devices/lastlog_storm.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_storm.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_storm.json", "r", errors='ignore') as log_file:
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
        print("File /var/log/devices/lastlog_storm.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_storm.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_storm.json - JSONDecodeError")
        exit()
 
 
    ## Sample Log
    ## swlogd intfCmm Mgr EVENT: CUSTLOG CMM Port 1\/1\/52 Storm Threshold violation - ingress traffic exceeds configured value 1
    ## On log if "ingress traffic exceeds configured value x" it does correspond to:
    ## Broadcast -  value 1
    ## Multicast - value 2
    ## Unknown unicast - value 3
    try:
        port, reason = re.findall(r"Port (.*?) Storm Threshold violation - ingress traffic exceeds configured value (.*)", msg)[0]
        port = port.replace("\'", "", 2)
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_storm.json - JSONDecodeError")
        exit()

        
    if reason == "1":
        reason = "Broadcast"
    elif reason == "2":
        reason = "Multicast"
    elif reason == "3":
        reason = "Unknown unicast"

# always 1
#never -1
# ? 0
syslog.syslog(syslog.LOG_INFO, "Executing function check_save") 
save_resp = check_save(ipadd, port, "storm")

function = "storm"
if script_has_run_recently(300,ipadd,function):
    print('you need to wait before you can run this again')
    syslog.syslog(syslog.LOG_INFO, "Executing script exit because executed within 5 minutes time period") 
    exit()


if save_resp == "0":
    syslog.syslog(syslog.LOG_INFO, "No Decision saved")
    answer = "0"
    syslog.syslog(syslog.LOG_INFO, "Executing function port_monitoring")
    port_monitoring(switch_user, switch_password, port, ipadd)
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_storm")
    filename_path, subject, action, result, category = collect_command_output_storm(switch_user, switch_password, port, reason, answer, host, ipadd)
    syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
    syslog.syslog(syslog.LOG_INFO, "Action: " + action)
    syslog.syslog(syslog.LOG_INFO, "Result: " + result)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
    send_file(filename_path, subject, action, result, category, jid)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

    notif = ("A {0} Storm Threshold violation occurs on OmniSwitch {1} / {2} port {3}.\nDo you want to disable this port?\nThe port-monitoring capture of port {3} is available on Server directory /tftpboot/").format(reason,host,ipadd,port)
#    notif = "A " + reason + " Storm Threshold violation occurs on OmniSwitch " + host + " port " + port + ". Do you want to disable this port? The port-monitoring capture of port " + port + " is available on Server " + ip_server + " directory /tftpboot/"
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card " + notif)
    answer = send_message_request(notif, jid)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            
    print(answer)
    sleep(2)
    #### Download port monitoring capture ###
    filename= '{0}_pmonitor_storm.enc'.format(host)
    remoteFilePath = '/flash/pmonitor.enc'
    localFilePath = "/tftpboot/{0}_{1}-{2}_{3}_{4}".format(date,date_hm.hour,date_hm.minute,ipadd,filename)
    try:
       syslog.syslog(syslog.LOG_INFO, "Executing function get_file_sftp - remoteFilePath: " + remoteFilePath + " localFilePath: " + localFilePath) 
       get_file_sftp(switch_user, switch_password, ipadd, remoteFilePath, localFilePath)
    except:
        pass
    if answer == "2":
        add_new_save(ipadd, port, "storm", choice="always")
        syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Port: " + port + " Choice: " + " Always")
 
    elif answer == "0":
        add_new_save(ipadd, port, "storm", choice="never")
        syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Port: " + port + " Choice: " + " Never")
elif save_resp == "-1":
    syslog.syslog(syslog.LOG_INFO, "Decision saved to No - script exit")
    notif = "Preventive Maintenance Application - A Storm Threshold violation has been detected on your network from the port {0} on device {1}.\nDecision saved for this switch/port is set to Never, we do not proceed further".format(port, ipadd, ip_server)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card " + notif)
    send_message(notif, jid)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
    try:
        print(port)
        print(reason)
        print(ipadd)
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Reason": reason, "port": port}, "fields": {"count": 1}}])
        syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        sys.exit()   
    except UnboundLocalError as error:
       print(error)
       sys.exit()
    except Exception as error:
       print(error)
       sys.exit() 

elif save_resp == "1":
    answer = '2'
    syslog.syslog(syslog.LOG_INFO, "Decision saved to Yes and remember")
    notif = "Preventive Maintenance Application - A Storm Threshold violation has been detected on your network from the port {0} on device {1}.\nDecision saved for this switch/port is set to Always, we do proceed for disabling the interface".format(port, ipadd, ip_server)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card " + notif)
    send_message(notif, jid)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
else:
    answer = '1'
    syslog.syslog(syslog.LOG_INFO, "No answer - Decision set to Yes")    

    notif = "Preventive Maintenance Application - A Storm Threshold violation has been detected on your network from the port {0} on device {1}.\nDecision saved for this switch/port is set to Always, we do proceed for disabling the interface".format(port, ipadd, ip_server)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card " + notif)
    send_message(notif, jid)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

if answer == '1':
    syslog.syslog(syslog.LOG_INFO, "Decision set to Yes - Interface is administratively disabled and log collected")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_storm")
    filename_path, subject, action, result, category = collect_command_output_storm(switch_user, switch_password, port, reason, answer, host, ipadd)
    syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
    syslog.syslog(syslog.LOG_INFO, "Action: " + action)
    syslog.syslog(syslog.LOG_INFO, "Result: " + result)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
    send_file(filename_path, subject, action, result, category, jid)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

elif answer == '2':
    syslog.syslog(syslog.LOG_INFO, "Decision set to Yes - Interface is administratively disabled")
    cmd = "interfaces port " + port + " admin-state disable"
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
    syslog.syslog(syslog.LOG_INFO, "SSH Session closed")
else:
    syslog.syslog(syslog.LOG_INFO, "No answer - Decision set to Yes - Script exit - will be called by next occurence")    


try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Reason": reason, "port": port}, "fields": {"count": 1}}])
    syslog.syslog(syslog.LOG_INFO, "Statistics saved")
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass 