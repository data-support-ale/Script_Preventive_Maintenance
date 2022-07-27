#!/usr/bin/env python3

import sys
import os
from xml.sax.handler import property_declaration_handler
from support_tools_OmniSwitch import debugging, get_credentials, ssh_connectivity_check, collect_command_output_lldp_port_description
import re  # Regex
import json
import time
import datetime
from support_send_notification import send_message_request_detailed, send_message_detailed
# from database_conf import *


from pattern import set_rule_pattern, set_portnumber, set_decision, get_decision, mysql_save

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path, os.pardir)))
sys.path.insert(1, os.path.abspath(os.path.join(path, os.pardir)))
from alelog import alelog

time.sleep(20)

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script :' + script_name)
_runtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
pattern = sys.argv[1]
print(pattern)
set_rule_pattern(pattern)
# info = ("We received following pattern from RSyslog {0}").format(pattern)
# os.system('logger -t montag -p user.info ' + info)

runtime = time.strftime("%d_%b_%Y_%H_%M_%S", time.localtime())

# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company, room_id = get_credentials()
subject = "A port flapping was detected in your network !"


def process(ip, hostname, port, agg):
    
    if port == "":
        set_portnumber(agg)
        decision = get_decision(ip)
        if (len(decision) == 0) or (len(decision) == 1 and decision[0] == 'Yes'):
            info = "A network loop has been detected on your network on the linkagg {} - System Description: N/A - OmniSwitch {}/{}.\nIf you click on Yes, the following actions will be done: Linkagg disable.".format(
            agg, ip, hostname)
            answer = send_message_request_detailed(info, jid1, jid2, jid3)
            set_decision(ip, answer)
            if answer == "2":
                answer = '1'
        elif 'No' in decision:
            sys.exit()
        else:
            answer = '1'
    else:
        set_portnumber(port)
        decision = get_decision(ip)
        lldp_port_description, _ = collect_command_output_lldp_port_description(switch_user, switch_password, port, ip)
        if (len(decision) == 0) or (len(decision) == 1 and decision[0] == 'Yes'):
            info = "A network loop has been detected on your network on the access port {} - System Description: {} - OmniSwitch {}/{}.\nIf you click on Yes, the following actions will be done: Port Admin Down.".format(
            port, lldp_port_description, ip, hostname)
            answer = send_message_request_detailed(info, jid1, jid2, jid3)
            set_decision(ip, answer)
            if answer == "2":
                answer = '1'
        elif 'No' in decision:
            sys.exit()
        else:
            answer = '1'

    if answer == '1':
        if port == "":
            cmd = "linkagg lacp agg " + agg + " admin-state disable"
            ssh_connectivity_check(switch_user, switch_password, ip, cmd)
            os.system(
                'logger -t montag -p user.info AggId {0} of OmniSwitch {1}/{2} updated'.format(port, agg, hostname))
            os.system('logger -t montag -p user.info Process terminated')
            info = "Preventive Maintenance Application - A network loop has been detected on your network and the linkagg {0} is administratively down on OmniSwitch {1}/{2}".format(agg, ip, hostname)
        else:
            cmd = "interface port " + port + " admin-state disable"
            ssh_connectivity_check(switch_user, switch_password, ip, cmd)
            os.system(
                'logger -t montag -p user.info Port {0} of OmniSwitch {1}/{2} updated'.format(port, port, hostname))
            os.system('logger -t montag -p user.info Process terminated')
            info = "Preventive Maintenance Application - A network loop has been detected on your network and the port {0} is administratively down on OmniSwitch {1}/{2}".format(port, ip, hostname)

        open('/var/log/devices/lastlog_loop.json', 'w').close()
        answer = send_message_detailed(info, jid1, jid2, jid3)
        mysql_save(runtime=_runtime, ip_address=ip, result='success', reason=info, exception='')
        # disable_debugging
        ipadd = ip
        appid = "bcmd"
        subapp = "all"
        level = "info"
        debugging(switch_user, switch_password,
                ipadd, appid, subapp, level)
        time.sleep(2)


counter = 0
last_time = ""
last_ip = ""
last_port = ""
last_mac = ""
text_file = ""
last_agg = ""

with open("/var/log/devices/lastlog_loop.json", "r", errors='ignore') as log_file:
    lines = log_file.readlines()
    for line in reversed(lines):
        try:
            line_json = json.loads(line)
            timestamp = (str(line_json["@timestamp"])[:19]).replace("T", " ").replace(":", " ").replace("-", " ")
            time = datetime.datetime.strptime(timestamp, "%Y %m %d %H %M %S")
            if counter == 0:
                last_time = time
                last_ip = line_json["relayip"]
                last_hostname = line_json["hostname"]
                msg = line_json["message"]
                if "aggId" in msg:
                    last_mac = re.findall(r"(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))", msg)[0][0]
                    last_agg = re.findall(r"aggId: (\d*)", msg)[0]
                    counter = 1
                else:
                    last_port = str(re.findall(r"(\d*/\d*/\d*)", msg)[0]).replace("\\", "")
                    counter = 1
                text_file = line
            elif time > (last_time - datetime.timedelta(seconds=10)): # reducing the file to a 10 sec window
                text_file = line + text_file
            else:
                break
                
        except json.decoder.JSONDecodeError:
            print("File /var/log/devices/lastlog_loop.json empty")
            exit()
        except IndexError:
            pass

with open("/var/log/devices/lastlog_loop.json", "w", errors='ignore') as log_file:
    log_file.write(text_file)

counter = 0 

with open("/var/log/devices/lastlog_loop.json", "r", errors='ignore') as log_file:
    for line in log_file:
        try:
            log_json = json.loads(line)
            ip = log_json["relayip"]
            hostname = log_json["hostname"]
            msg = log_json["message"]
            port = "null"
            agg = "null"
            if ip == last_ip:
                if "aggId" in msg:
                    agg = re.findall(r"aggId: (\d*)", msg)[0]
                elif last_mac != "" : # line is a normal port, we check if moving MAC correspond
                    mac = re.findall(r"(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))", msg)[0][0]
                    if mac == last_mac:
                        last_port = str(re.findall(r"(\d*/\d*/\d*)", msg)[0]).replace("\\", "")
                        last_mac = ""
                else:
                    port = str(re.findall(r"(\d*/\d*/\d*)", msg)[0]).replace("\\", "")

                print("log: {}".format(ip))
        except json.decoder.JSONDecodeError:
            print("File /var/log/devices/lastlog_loop.json empty")
            exit()
        except IndexError:
            pass

        if port == last_port or agg == last_agg:
            counter += 1
            print(counter)
            
        if(counter == 1): # Number of occurences needed to trigger
            process(ip, hostname, last_port, last_agg)
            break