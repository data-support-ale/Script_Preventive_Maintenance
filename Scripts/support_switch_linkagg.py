#!/usr/local/bin/python3.7

import sys
import os
import re
import json
from support_tools_OmniSwitch import collect_command_output_linkagg, get_credentials, send_file, script_has_run_recently, get_file_sftp, port_monitoring, collect_command_output_lldp_port_description, ssh_connectivity_check, get_arp_entry
from time import sleep
import datetime
from support_send_notification import send_message_request, send_message, send_message_request_advanced
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
with open("/var/log/devices/lastlog_linkagg.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_linkagg.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_linkagg.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ip = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_linkagg.json empty")
        exit()
    except IndexError:
        print("Index error in regex")
        exit()
 
 
    ## Sample Log
    ## OS6860E_VC_Core swlogd linkAggCmm main INFO: Receive agg port leave request: agg: 1, port: 1/1/1(0)
    os.system('logger -t montag -p user.info Executing script support_switch_linkagg - start')
    try:
        agg, port = re.findall(r"Receive agg port leave request: agg: (.*?), port:(.*?)\(", msg)[0]
        print(port)
    except IndexError:
        print("Index error in regex")
        os.system('logger -t montag -p user.info Executing script support_switch_linkagg - Index error in regex')
        exit()
        
# always 1
#never -1
# ? 0
save_resp = check_save(ip,port, "linkagg")

function = "linkagg"
if script_has_run_recently(300,ip,function):
    print('you need to wait before you can run this again')
    os.system('logger -t montag -p user.info Executing script exit because executed within 5 minutes time period')
    exit()


if save_resp == "0":
    answer = "0"
    port_monitoring(switch_user, switch_password, port, ip)
    notif = "A LinkAgg Port Leave occurs on OmniSwitch " + host + " port " + port + " LinkAgg " + agg
    send_message(notif, jid)   
    lldp_port_description, lldp_mac_address = collect_command_output_lldp_port_description(switch_user, switch_password, port, ip)  
    if lldp_port_description == 0:
        device_type = 0
        filename_path, subject, action, result, category = collect_command_output_linkagg(switch_user, switch_password, agg, host, ip)
        send_file(filename_path, subject, action, result, category) 
    elif "OAW-AP" in str(lldp_port_description):
        # If LLDP Remote System is Stellar AP we search for IP Address in ARP Table
        device_ip = get_arp_entry(switch_user, switch_password, lldp_mac_address, ip)
        device_type = "OAW-AP"
        notif = "A LinkAgg Port Leave occurs on OmniSwitch " + host + " port " + port + " LinkAgg " + agg + " - Port Description: " + lldp_port_description + ". Stellar AP " + device_ip + "/" + lldp_mac_address + " is connected to this port, do you want to collect AP logs? The port-monitoring capture of port " + port + " is available on Server " + ip_server + " directory /tftpboot/"
        # If LLDP Remote System is Stellar AP we propose to collect AP Logs
        answer = send_message_request(notif, jid)      
    else:
        device_type = "Others"
        filename_path, subject, action, result, category = collect_command_output_linkagg(switch_user, switch_password, agg, host, ip)
        action = "A LinkAgg Port Leave occurs on OmniSwitch " + host + " port " + port + " LinkAgg " + agg + " - Port Description: " + lldp_port_description + ". The port-monitoring capture of port " + port + " is available on Server " + ip_server + " directory /tftpboot/"
        send_file(filename_path, subject, action, result, category) 
    print(answer)
    sleep(2)
    #### Download port monitoring capture ###
    filename= '{0}_pmonitor_linkagg.enc'.format(host)
    remoteFilePath = '/flash/pmonitor.enc'
    localFilePath = "/tftpboot/{0}_{1}-{2}_{3}_{4}".format(date,date_hm.hour,date_hm.minute,ip,filename)
    try: 
       get_file_sftp(switch_user, switch_password, ip, remoteFilePath, localFilePath)
    except:
        pass
    if answer == "2":
        add_new_save(ip,port, "linkagg", choice="always")
    elif answer == "0":
        add_new_save(ip,port, "linkagg", choice="never")
elif save_resp == "-1":
    info = "A LinkAgg Port Leave has been detected on your network from the port {0}/Agg {1} on device {2}. Decision saved for this switch/port is set to Never, we do not proceed further".format(port, agg, ip)
    send_message(info,jid)
    try:
        print(port)
        print(agg)
        print(ip)
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ip, "LinkAgg": agg, "port": port}, "fields": {"count": 1}}])
        sys.exit()   
    except UnboundLocalError as error:
       print(error)
       sys.exit()
    except Exception as error:
       print(error)
       sys.exit() 

elif save_resp == "1":
    answer = '2'
    info = "A LinkAgg Port Leave has been detected on your network from the port {0} on device {1}. Decision saved for this switch/port is set to Always, we do proceed for disabling the interface".format(port, ip, ip_server)
    send_message(info,jid)
else:
    info = "A LinkAgg Port Leave has been detected on your network from the port {0} on device {1}. Decision saved for this switch/port is set to Always, we do proceed for disabling the interface".format(port, ip, ip_server)
    send_message(info,jid)

if answer == '1':
    if device_type == "OAW-AP":
        os.system('logger -t montag -p user.info Collecting Snapshot logs on Stellar AP')
        cmd = "ssudo tech_support_command 12 " + ip_server
        ssh_connectivity_check(login_AP, pass_AP, device_ip, cmd)
        os.system('logger -t montag -p user.info Collecting logs on OmniSwitch')
        filename_path, subject, action, result, category = collect_command_output_linkagg(switch_user, switch_password, agg, host, ip)
        send_file(filename_path, subject, action, result, category)
    else:
        os.system('logger -t montag -p user.info Collecting logs on OmniSwitch')
        filename_path, subject, action, result, category = collect_command_output_linkagg(switch_user, switch_password, agg, host, ip)
        send_file(filename_path, subject, action, result, category)

elif answer == '2':
    os.system('logger -t montag -p user.info Process terminated')
    cmd = "clear violation port " + port
    os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
        switch_password, switch_user, ip, cmd))

else:
    print("Mail request set as no")
    os.system('logger -t montag -p user.info Mail request set as no')
    sleep(1)

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ip, "LinkAgg": agg, "port": port}, "fields": {"count": 1}}])
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass 