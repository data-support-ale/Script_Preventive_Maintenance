#!/usr/bin/env python3

import sys
import os
from xml.sax.handler import property_declaration_handler
from support_tools_OmniSwitch import debugging, get_credentials, ssh_connectivity_check, collect_command_output_lldp_port_description, collect_command_output_flapping, collect_command_output_lldp_port_capability, isUpLink
from time import strftime, localtime, sleep
import re  # Regex
import json
from datetime import datetime, timedelta
from support_send_notification import send_message_request, send_message, send_message_request_advanced
# from database_conf import *
import time
import syslog

syslog.openlog('support_switch_port_flapping')
syslog.syslog(syslog.LOG_INFO, "Executing script")


from pattern import set_rule_pattern, set_portnumber, set_decision, get_decision, mysql_save

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path, os.pardir)))
sys.path.insert(1, os.path.abspath(os.path.join(path, os.pardir)))
from alelog import alelog


# Script init
script_name = sys.argv[0]
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
pattern = sys.argv[1]
print(pattern)
set_rule_pattern(pattern)

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company, room_id = get_credentials()

def process(ip, hostname, port, link):
    lldp_port_description = status_changes = link_quality = ""
    syslog.syslog(syslog.LOG_INFO, "Executing function get_decision")
    decision = get_decision(ip)
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_lldp_port_description")
    lldp_port_description, _ = collect_command_output_lldp_port_description(switch_user, switch_password, port, ip)
    syslog.syslog(syslog.LOG_INFO, "LLDP Port Description collected: " + lldp_port_description)
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_flapping")
    status_changes, link_quality = collect_command_output_flapping(switch_user, switch_password, port, ip)
    syslog.syslog(syslog.LOG_INFO, "Status changes collected: " + status_changes)
    syslog.syslog(syslog.LOG_INFO, "Link Quality collected: " + link_quality)
    if link == "UPLINK":
        syslog.syslog(syslog.LOG_INFO, "Link is an UpLink")
        notif = "A port flapping has been detected on your network on the UPLINK port {0} on OmniSwitch {1}/{2}\nInterface details :\
        \n- System Description : {3}\n- Number of Status Change : {4}\n- Link-Quality : {5}\n\nPlease check the number of status \
        change and Link-Quality level (command show interfaces port x/x/x status).\nWe could consider this issue is related to \
        a Layer 1 connectivity issue and SFP/Cable shall be replaced.\n".format(port, hostname, ip, lldp_port_description, status_changes, link_quality)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send Notification")
        send_message(notif)
        set_decision(ip, "4")
        mysql_save(runtime=_runtime, ip_address=ip, result='success', reason=notif, exception='')

    else:

        if (len(decision) == 0) or (len(decision) == 1 and decision[0] == 'Yes'):
            syslog.syslog(syslog.LOG_INFO, "No Decision saved")
            if lldp_port_description == 0:
                syslog.syslog(syslog.LOG_INFO, "LLDP Port Description is empty")
                notif = "A port flapping has been detected on your network on the access port {0} - System Description: N/A - Number of Status Change : {2} - Link Quality : {3} on OmniSwitch {4}/{5}.\nIf you click on Yes, the following actions will be done: Port Admin Down/Up.".format(port, lldp_port_description, status_changes, link_quality, ip, hostname)
                syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Rainbow Adaptive Card Advanced")
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                answer = send_message_request_advanced(notif, "Admin down")
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent - Adaptive Card answer: " + answer)
                set_decision(ip, answer)
                mysql_save(runtime=_runtime, ip_address=ip, result='success', reason=notif + "Decision received: " + answer, exception='')
            else:
                notif = "Preventive Maintenance Application - A port flapping has been detected on your network on the access port {0} - System Description: {1} - Number of Status Change : {2} - Link Quality : {3} on OmniSwitch {4}/{5}.\nIf you click on Yes, the following actions will be done: Port Admin Down/Up.".format(port, lldp_port_description, status_changes, link_quality, ip, hostname)
                syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Rainbow Adaptive Card")
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                answer = send_message_request_advanced(notif, "Admin down")
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent - Adaptive Card answer: " + answer)
                set_decision(ip, answer)
                mysql_save(runtime=_runtime, ip_address=ip, result='success', reason=notif + "Decision received: " + answer, exception='')
        elif 'No' in decision:
            print("Decision saved to No - script exit")
            syslog.syslog(syslog.LOG_INFO, "Decision saved to No - script exit") 
            sys.exit()   

        elif 'yes and remember' in [d.lower() for d in decision]:
            answer = '2'
            print("Decision saved to Yes and remember")
            syslog.syslog(syslog.LOG_INFO, "Decision saved to Yes and remember")
        else:
            answer = '1'
            syslog.syslog(syslog.LOG_INFO, "No answer - Decision set to Yes - Script exit - will be called by next occurence")    

        syslog.syslog(syslog.LOG_INFO, "Rainbow Acaptive Card answer: " + answer)

        if answer == '1':
            syslog.syslog(syslog.LOG_INFO, "Decision set to Yes - Port toggle")
            cmd = "interfaces port " + port + " admin-state disable; sleep 1; interfaces port " + port + " admin-state enable"
            syslog.syslog(syslog.LOG_INFO, "SSH Session start")
            syslog.syslog(syslog.LOG_INFO, "Command executed: " + cmd) 
            ssh_connectivity_check(switch_user, switch_password, ip, cmd)
            syslog.syslog(syslog.LOG_INFO, "SSH Session end")
            notif = "Preventive Maintenance Application - A port flapping has been detected on your network and the port {0} is administratively updated  on OmniSwitch {1}/{2}".format(port, ip, hostname)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send Notification")
            send_message(notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            set_decision(ip, "4")
            mysql_save(runtime=_runtime, ip_address=ip, result='success', reason=notif, exception='')
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            # disable_debugging
            appid = "bcmd"
            subapp = "all"
            level = "info"
            syslog.syslog(syslog.LOG_INFO, "Script executing function debugging - swlog appid bcmd subapp all level info")
            debugging(switch_user, switch_password,ip, appid, subapp, level)
            sleep(2)

        if answer == '3':
            syslog.syslog(syslog.LOG_INFO, "Decision set to Admin Down")
            cmd = "interfaces port " + port + " admin-state disable"
            syslog.syslog(syslog.LOG_INFO, "SSH Session start")
            syslog.syslog(syslog.LOG_INFO, "Command executed: " + cmd) 
            ssh_connectivity_check(switch_user, switch_password, ip, cmd)
            syslog.syslog(syslog.LOG_INFO, "SSH Session end")
            notif = "Preventive Maintenance Application - A port flapping has been detected on your network and the port {0} is administratively down  on OmniSwitch {1}/{2}".format(port, ip, hostname)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send Notification")            
            send_message(notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            set_decision(ip, "4")
            mysql_save(runtime=_runtime, ip_address=ip, result='success', reason=notif, exception='')
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            # disable_debugging
            appid = "bcmd"
            subapp = "all"
            level = "info"
            syslog.syslog(syslog.LOG_INFO, "Script executing function debugging - swlog appid bcmd subapp all level info")
            debugging(switch_user, switch_password,ip, appid, subapp, level)
            sleep(2)

        else:
            print("No decision matching - script exit")
            syslog.syslog(syslog.LOG_INFO, "No decision matching - script exit")
            sys.exit()

# Script init
script_name = sys.argv[0]
# os.system('logger -t montag -p user.info Executing script :' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
notif = "A port flapping was detected in your network !"
syslog.syslog(syslog.LOG_INFO, notif)
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

with open("/var/log/devices/lastlog_flapping.json", "r", errors='ignore') as log_file:
    for line in log_file:
        try:
            log_json = json.loads(line)
            ip = log_json["relayip"]
            hostname = log_json["hostname"]
            msg = log_json["message"]
            port, state = re.findall(r"LINKSTS (.*?) (UP|DOWN)", msg)[0]
            print("log: {} {}".format(ip, port))
            print(msg)
            syslog.syslog(syslog.LOG_DEBUG, "Syslog IP Address: " + ip)
            syslog.syslog(syslog.LOG_DEBUG, "Syslog Hostname: " + hostname)
            syslog.syslog(syslog.LOG_DEBUG, "Syslog port: " + port)
            #syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + msg)
        except json.decoder.JSONDecodeError:
            print("File /var/log/devices/lastlog_flapping.json empty")
            syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_flapping.json - JSONDecodeError")
            exit()
        except IndexError:
            print("Index error in regex")
            syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_flapping.json - IndexError")
            exit()

        if(ip == last_ip and port == last_port):
            counter+= 1
            print(counter)
            syslog.syslog(syslog.LOG_DEBUG, "If ipadd equals to last_ip and port equals to last_port we increment the counter")
            syslog.syslog(syslog.LOG_DEBUG, "Counter: " + str(counter))
        if(counter == 5):
            set_portnumber(port)
            syslog.syslog(syslog.LOG_DEBUG, "5 Port Flapping occurences detected - script executing function collect_command_output_lldp_port_capability")
            lldp_port_capability = collect_command_output_lldp_port_capability(switch_user, switch_password, port, ip)
            syslog.syslog(syslog.LOG_DEBUG, "LLDP Port Capability: " + lldp_port_capability)
            if("Router" in str(lldp_port_capability) or "Bridge" in str(lldp_port_capability)):
                syslog.syslog(syslog.LOG_DEBUG, "Executing function process - Link UPLINK")
                process(ip, hostname, port, "UPLINK")
            elif(isUpLink(switch_user, switch_password, port, ip)):
                syslog.syslog(syslog.LOG_DEBUG, "Executing function process - Link UPLINK")
                process(ip, hostname, port, "UPLINK")
            else:
                syslog.syslog(syslog.LOG_DEBUG, "Executing function process - Link ACCESS")
                process(ip, hostname, port, "ACCESS")
            break
