#!/usr/local/bin/python3.7

import ipaddress
from itertools import count
import sys
import json

from prometheus_client import Histogram
from support_tools_OmniSwitch import collect_command_output_lldp_port_capability, debugging, get_credentials, isUpLink, collect_command_output_lldp_port_description, add_new_save, check_save, collect_command_output_flapping, ssh_connectivity_check,script_has_run_recently
from time import strftime, localtime, sleep
from datetime import datetime, timedelta
import re
from support_send_notification import send_message_detailed, send_message_request_advanced
from database_conf import *
import syslog

syslog.openlog('support_switch_port_flapping')
syslog.syslog(syslog.LOG_INFO, "Executing script")



def process(ipadd, hostname, port, link):
    lldp_port_description = status_changes = link_quality = ""
    try:
        write_api.write(bucket, org, [{"measurement": "support_switch_port_flapping.py", "tags": {"IP_Address": ipadd, "Port": port}, "fields": {"count": 1}}])
        syslog.syslog(syslog.LOG_INFO, "Statistics saved")
    except UnboundLocalError as error:
        print(error)
        syslog.syslog(syslog.LOG_INFO, "Exception - script exit " + error)
        sys.exit()
    except Exception as error:
        print(error)
        syslog.syslog(syslog.LOG_INFO, "Exception: " + error)
        pass 
        syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_lldp_port_description")
        lldp_port_description, _ = collect_command_output_lldp_port_description(switch_user, switch_password, port, ipadd)
        syslog.syslog(syslog.LOG_INFO, "LLDP Port Description collected: " + lldp_port_description)
        syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_flapping")
        status_changes, link_quality = collect_command_output_flapping(switch_user, switch_password, port, ipadd)
        syslog.syslog(syslog.LOG_INFO, "Status changes collected: " + status_changes)
        syslog.syslog(syslog.LOG_INFO, "Link Quality collected: " + link_quality)

    syslog.syslog(syslog.LOG_INFO, "Executing function check_save")
    save_resp = check_save(ipadd, port, "flapping")
    syslog.syslog(syslog.LOG_INFO, "check_save result: " + save_resp)

    if link == "UPLINK":
        syslog.syslog(syslog.LOG_INFO, "Link is an UpLink")
        notif = "A port flapping has been detected on your network on the UPLINK port {0} on OmniSwitch {1}/{2}\nInterface details :\
        \n- System Description : {3}\n- Number of Status Change : {4}\n- Link-Quality : {5}\n\nPlease check the number of status \
        change and Link-Quality level (command show interfaces port x/x/x status).\nWe could consider this issue is related to \
        a Layer 1 connectivity issue and SFP/Cable shall be replaced.\n".format(port, hostname, ipadd, lldp_port_description, status_changes, link_quality)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send Notification")
        send_message_detailed(notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        
    else:

        if save_resp == "0":
            syslog.syslog(syslog.LOG_INFO, "No Decision saved")
            if lldp_port_description == 0:
                syslog.syslog(syslog.LOG_INFO, "LLDP Port Description is empty")
                notif = "A port flapping has been detected on your network on the access port {0} - System Description: N/A - Number of Status Change : {2} - Link Quality : {3} on OmniSwitch {4}/{5}.\nIf you click on Yes, the following actions will be done: Port Admin Down/Up.".format(port, lldp_port_description, status_changes, link_quality, ipadd, hostname)
                syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Rainbow Adaptive Card Advanced")
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                answer = send_message_request_advanced(notif, "Admin down")
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent - Adaptive Card answer: " + answer)

            else:
                notif = "Preventive Maintenance Application - A port flapping has been detected on your network on the access port {0} - System Description: {1} - Number of Status Change : {2} - Link Quality : {3} on OmniSwitch {4}/{5}.\nIf you click on Yes, the following actions will be done: Port Admin Down/Up.".format(port, lldp_port_description, status_changes, link_quality, ipadd, hostname)
                syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Rainbow Adaptive Card")
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                answer = send_message_request_advanced(notif, "Admin down")
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent - Adaptive Card answer: " + answer)

            if answer == "2":
                add_new_save(ipadd, port, "flapping", choice="always")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Port: " + port + " Choice: " + " Always")
                answer = '1'
            elif answer == "0":
                add_new_save(ipadd, port, "flapping", choice="never")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Port: " + port + " Choice: " + " Never")
        elif save_resp == "-1":
            syslog.syslog(syslog.LOG_INFO, "Decision saved to No - script exit")
            sys.exit()
        elif save_resp == "1":
            answer = '2'
            print("Decision saved to Yes and remember")
            syslog.syslog(syslog.LOG_INFO, "Decision saved to Yes and remember")
        else:
            answer = '1'
            syslog.syslog(syslog.LOG_INFO, "No answer - Decision set to Yes - Script exit - will be called by next occurence")    

        if answer == '1':
            syslog.syslog(syslog.LOG_INFO, "Decision set to Yes - Port toggle")
            cmd = "interfaces port " + port + " admin-state disable; sleep 1; interfaces port " + port + " admin-state enable"
            syslog.syslog(syslog.LOG_INFO, "SSH Session start")
            syslog.syslog(syslog.LOG_INFO, "Command executed: " + cmd) 
            ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
            syslog.syslog(syslog.LOG_INFO, "SSH Session end")
            try:
                syslog.syslog(syslog.LOG_INFO, "Port" + port + "of OmniSwitch" + hostname + "/" + ipadd + "is toggled")
            except:
                print("logging failure")
                pass


            notif = "Preventive Maintenance Application - A port flapping has been detected on your network and the port {0} is administratively updated  on OmniSwitch {1}/{2}".format(port, ipadd, hostname)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send Notification")
            send_message_detailed(notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            # disable_debugging
            ipadd = ipadd
            appid = "bcmd"
            subapp = "all"
            level = "info"
            syslog.syslog(syslog.LOG_INFO, "Script executing function debugging - swlog appid bcmd subapp all level info")
            debugging(switch_user, switch_password,
                    ipadd, appid, subapp, level)
            # disable_debugging
            ipadd = ipadd
            debugging(switch_user, switch_password,
                    ipadd, appid, subapp, level)
            sleep(2)

        if answer == '3':
            syslog.syslog(syslog.LOG_INFO, "Decision set to Admin Down")
            cmd = "interfaces port " + port + " admin-state disable"
            syslog.syslog(syslog.LOG_INFO, "SSH Session start")
            syslog.syslog(syslog.LOG_INFO, "Command executed: " + cmd) 
            ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
            syslog.syslog(syslog.LOG_INFO, "SSH Session end")
            try:
                syslog.syslog(syslog.LOG_INFO, "Port" + port + "of OmniSwitch" + hostname + "/" + ipadd + "is administratively disabled")
            except:
                print("logging failure")
                pass
            notif = "Preventive Maintenance Application - A port flapping has been detected on your network and the port {0} is administratively down  on OmniSwitch {1}/{2}".format(port, ipadd, hostname)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send Notification")
            send_message_detailed(notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")


            # disable_debugging
            ipadd = ipadd
            appid = "bcmd"
            subapp = "all"
            level = "info"
            syslog.syslog(syslog.LOG_INFO, "Script executing function debugging - swlog appid bcmd subapp all level info")
            debugging(switch_user, switch_password,ipadd, appid, subapp, level)
            # disable_debugging
            ipadd = ipadd
            debugging(switch_user, switch_password,ipadd, appid, subapp, level)
            sleep(2)

# Script init
script_name = sys.argv[0]
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()
subject = "A port flapping was detected in your network !"
syslog.syslog(syslog.LOG_INFO, subject)

counter = 0
last_time = ""
last_ip = ""
last_port = ""

text_file = ""

with open("/var/log/devices/lastlog_flapping.json", "r", errors='ignore') as log_file:
    lines = log_file.readlines()
    for line in reversed(lines):
        try:
            line_json = json.loads(line)
            timestamp = (str(line_json["@timestamp"])[:19]).replace("T", " ").replace(":", " ").replace("-", " ")
            time = datetime.strptime(timestamp, "%Y %m %d %H %M %S")
            if counter == 0:
                counter = 1
                last_time = time
                last_ip = line_json["relayip"]
                msg = line_json["message"]
                last_port, _ = re.findall(r"LINKSTS (.*?) (UP|DOWN)", msg)[0]
                print(msg)
                syslog.syslog(syslog.LOG_DEBUG, "Syslog Last IP Address: " + last_ip)
                syslog.syslog(syslog.LOG_DEBUG, "Syslog Last port: " + last_port)
                #syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + msg)
                text_file = line
            elif time > (last_time - timedelta(seconds=20)):
                text_file = line + text_file
                
        except json.decoder.JSONDecodeError:
            print("File /var/log/devices/lastlog_flapping.json empty")
            syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_flapping.json - JSONDecodeError")
            exit()
        except IndexError:
            print("Index error in regex")
            syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_flapping.json - Index error in regex")
            exit()

with open("/var/log/devices/lastlog_flapping.json", "w", errors='ignore') as log_file:
    log_file.write(text_file)

counter = 0
function = "flapping"
if script_has_run_recently(30, last_ip,function):
    print('you need to wait before you can run this again')
    syslog.syslog(syslog.LOG_DEBUG, "Executing script exit because executed within 30 sec time period")
    exit()

with open("/var/log/devices/lastlog_flapping.json", "r", errors='ignore') as log_file:
    for line in log_file:
        try:
            log_json = json.loads(line)
            ipadd = log_json["relayip"]
            hostname = log_json["hostname"]
            msg = log_json["message"]
            port, state = re.findall(r"LINKSTS (.*?) (UP|DOWN)", msg)[0]
            print("log: {} {}".format(ipadd, port))
            print(msg)
            syslog.syslog(syslog.LOG_DEBUG, "Syslog IP Address: " + ipadd)
            syslog.syslog(syslog.LOG_DEBUG, "Syslog Hostname: " + hostname)
            syslog.syslog(syslog.LOG_DEBUG, "Syslog port: " + port)
            #syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + msg)
        except json.decoder.JSONDecodeError:
            print("File /var/log/devices/lastlog_flapping.json empty")
            syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_flapping.json - JSONDecodeError")
            exit()
        except IndexError:
            print("Index error in regex")
            syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_flapping.json - JSONDecodeError")
            exit()

        if(ipadd == last_ip and port == last_port):
            counter+= 1
            print(counter)
            syslog.syslog(syslog.LOG_DEBUG, "If ipadd equals to last_ip and port equals to last_port we increment the counter")
            syslog.syslog(syslog.LOG_DEBUG, "Counter: " + str(counter))
        if(counter == 5):
            #set_portnumber(port)
            syslog.syslog(syslog.LOG_DEBUG, "5 Port Flapping occurences detected - script executing function collect_command_output_lldp_port_capability")
            lldp_port_capability = collect_command_output_lldp_port_capability(switch_user, switch_password, port, ipadd)
            syslog.syslog(syslog.LOG_DEBUG, "LLDP Port Capability: " + lldp_port_capability)
            if("Router" in str(lldp_port_capability) or "Bridge" in str(lldp_port_capability)):
                syslog.syslog(syslog.LOG_DEBUG, "Executing function process - Link UPLINK")
                process(ipadd, hostname, port, "UPLINK")
            elif(isUpLink(switch_user, switch_password, port, ipadd)):
                syslog.syslog(syslog.LOG_DEBUG, "Executing function process - Link UPLINK")
                process(ipadd, hostname, port, "UPLINK")
            else:
                syslog.syslog(syslog.LOG_DEBUG, "Executing function process - Link ACCESS")
                process(ipadd, hostname, port, "ACCESS")
            break
