#!/usr/local/bin/python3.7

import sys
import os
import re
import json
from support_tools_OmniSwitch import get_credentials, collect_command_output_storm, send_file, script_has_run_recently, get_file_sftp, port_monitoring
from time import sleep
import datetime
from support_send_notification import send_message_request, send_message
from database_conf import *
from support_tools_OmniSwitch import add_new_save, check_save
import requests

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
#runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())


# Get informations from logs.
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
        ip = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_storm.json empty")
        exit()
    except IndexError:
        print("Index error in regex")
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
save_resp = check_save(ip, port, "storm")

function = "storm"
if script_has_run_recently(300,ip,function):
    print('you need to wait before you can run this again')
    os.system('logger -t montag -p user.info Executing script exit because executed within 5 minutes time period')
    exit()


if save_resp == "0":
    answer = "0"
    port_monitoring(switch_user, switch_password, port, ip)
    filename_path, subject, action, result, category = collect_command_output_storm(switch_user, switch_password, port, reason, answer, host, ip)
    send_file(filename_path, subject, action, result, category)
    notif = "A " + reason + " Storm Threshold violation occurs on OmniSwitch " + host + " port " + port + ". Do you want to disable this port? The port-monitoring capture of port " + port + " is available on Server " + ip_server + " directory /tftpboot/"
    answer = send_message_request(notif, jid)
    print(answer)
    sleep(2)
    #### Download port monitoring capture ###
    filename= '{0}_pmonitor_storm.enc'.format(host)
    remoteFilePath = '/flash/pmonitor.enc'
    localFilePath = "/tftpboot/{0}_{1}-{2}_{3}_{4}".format(date,date_hm.hour,date_hm.minute,ip,filename)
    try: 
       get_file_sftp(switch_user, switch_password, ip, remoteFilePath, localFilePath)
    except:
        pass
    if answer == "2":
        add_new_save(ip, port, "storm", choice="always")
    elif answer == "0":
        add_new_save(ip, port, "storm", choice="never")
elif save_resp == "-1":
    info = "A Storm Threshold violation has been detected on your network from the port {0} on device {1}. Decision saved for this switch/port is set to Never, we do not proceed further".format(port, ip, ip_server)
    send_message(info,jid)
    try:
        print(port)
        print(reason)
        print(ip)
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ip, "Reason": reason, "port": port}, "fields": {"count": 1}}])
        sys.exit()   
    except UnboundLocalError as error:
       print(error)
       sys.exit()
    except Exception as error:
       print(error)
       sys.exit() 

elif save_resp == "1":
    answer = '2'
    info = "A Storm Threshold violation has been detected on your network from the port {0} on device {1}. Decision saved for this switch/port is set to Always, we do proceed for disabling the interface".format(port, ip, ip_server)
    send_message(info,jid)
else:
    info = "A Storm Threshold violation has been detected on your network from the port {0} on device {1}. Decision saved for this switch/port is set to Always, we do proceed for disabling the interface".format(port, ip, ip_server)
    send_message(info,jid)

if answer == '1':
    os.system('logger -t montag -p user.info Process terminated')
    # CLEAR VIOLATION
    filename_path, subject, action, result, category = collect_command_output_storm(switch_user, switch_password, port, reason, answer, host, ip)
    #cmd = "clear violation port " + port
    #os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user, ip, cmd))
    
    send_file(filename_path, subject, action, result, category)
    #info = "A port Storm violation has been cleared up on device {}".format(ip)
    #send_message(info, jid)

elif answer == '2':
    os.system('logger -t montag -p user.info Process terminated')
    # CLEAR VIOLATION
    cmd = "clear violation port " + port
    os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
        switch_password, switch_user, ip, cmd))

else:
    print("Mail request set as no")
    os.system('logger -t montag -p user.info Mail request set as no')
    sleep(1)

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                    "IP": ip, "Reason": reason, "port": port}, "fields": {"count": 1}}])
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass 