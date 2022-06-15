#!/usr/local/bin/python3.7

from itertools import count
import sys
import json

from prometheus_client import Histogram
from support_tools_OmniSwitch import collect_command_output_lldp_port_capability, debugging, get_credentials, isUpLink, collect_command_output_lldp_port_description, add_new_save, disable_port, enable_port, check_save, collect_command_output_flapping
from time import strftime, localtime, sleep
from datetime import datetime
import re
from support_send_notification import send_message, send_message_request_advanced
from database_conf import *


def process(ip, hostname, port, link):
    save_resp = check_save(ip, port, "flapping")

    if link == "UPLINK":
        lldp_port_description, _ = collect_command_output_lldp_port_description(
        switch_user, switch_password, port, ip)

        status_changes, link_quality = collect_command_output_flapping(switch_user, switch_password, port, ip)
        info = "A port flapping has been detected on your network on the port {0} of OmniSwitch {1}/{2}\nInterface details :\
        \n- System Description : {3}\n- Number of Status Change : {4}\n- Link-Quality : {5}\n\nPlease check the number of status \
        change and Link-Quality level (command show interfaces port x/x/x status).\nWe could consider this issue is related to \
        a Layer 1 connectivity issue and SFP/Cable shall be replaced.\nIf you click on Yes, the following actions will be done: Port Admin Down/Up".format(port, hostname, ip, lldp_port_description, status_changes, link_quality)
        send_message(info, jid)
        
    else:

        if save_resp == "0":
            lldp_port_description, _ = collect_command_output_lldp_port_description(
                switch_user, switch_password, port, ip)
            info = "A port flapping has been detected on your network on  the port {0} - System Description: {1} of OmniSwitch {2}/{3}. (if you click on Yes, the following actions will be done: Port Admin Down/Up)".format(
                port, lldp_port_description, ip, hostname)
            answer = send_message_request_advanced(info, jid, "Admin down")
            if answer == "2":
                add_new_save(ip, port, "flapping", choice="always")
                answer = '1'
            elif answer == "0":
                add_new_save(ip, port, "flapping", choice="never")
        elif save_resp == "-1":
            sys.exit()
        else:
            answer = '1'

        if answer == '1':
            disable_port(switch_user, switch_password,ip, port)
            os.system(
                'logger -t montag -p user.info Port {0} of OmniSwitch {1}/{2} disable'.format(port, ip, hostname))

            enable_port(switch_user, switch_password,ip, port)
            os.system(
                'logger -t montag -p user.info Port {0} of OmniSwitch {1}/{2} enable'.format(port, ip, hostname))

            os.system('logger -t montag -p user.info Process terminated')

            if jid != '':
                #info = "Log of device : {0}".format(ip)
                #send_file(info, jid, ip)
                sleep(1)
                #info = "Log of device : {0}".format(ip)
                #send_file(info, jid, ip)
                info = "A port flapping has been detected on your network and the port {0} is administratively updated  of OmniSwitch {1}/{2}, the port {3}  is administratively updated  on device {4}".format(
                    port, ip, hostname, port, ip)
                send_message(info, jid)

            # disable_debugging
            ipadd = ip
            appid = "bcmd"
            subapp = "all"
            level = "info"
            debugging(switch_user, switch_password,
                    ipadd, appid, subapp, level)
            # disable_debugging
            ipadd = ip
            debugging(switch_user, switch_password,
                    ipadd, appid, subapp, level)
            sleep(2)



        if answer == '3':
            disable_port(switch_user, switch_password,
                        ip, port)
            os.system(
                'logger -t montag -p user.info Port {0} of OmniSwitch {1}/{2} disable'.format(port, ip, hostname))

            if jid != '':
                #info = "Log of device : {0}".format(ip)
                #send_file(info, jid, ip)
                sleep(1)
                #info = "Log of device : {0}".format(ip)
                #send_file(info, jid, ip)
                info = "A port flapping has been detected on your network and the port {0} is administratively down  of OmniSwitch {1}/{2}, the port {3}  is administratively down  on device {4}".format(
                    port, ip, hostname, port, ip)
                send_message(info, jid)

            # disable_debugging
            ipadd = ip
            appid = "bcmd"
            subapp = "all"
            level = "info"
            debugging(switch_user, switch_password,
                    ipadd, appid, subapp, level)
            # disable_debugging
            ipadd = ip
            debugging(switch_user, switch_password,
                    ipadd, appid, subapp, level)
            sleep(2)

# Script init
script_name = sys.argv[0]
#os.system('logger -t montag -p user.info Executing script :' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()
subject = "A port flapping was detected in your network !"

counter = 0
last = ""

with open("/var/log/devices/lastlog_flapping.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line
try:
    last = json.loads(last)
    last_ip = last["relayip"]
    msg = last["message"]
    last_port, _ = re.findall(r"LINKSTS (.*?) (UP|DOWN)", msg)[0]
except json.decoder.JSONDecodeError:
    print("File /var/log/devices/lastlog_flapping.json empty")
    exit()
except IndexError:
    print("Index error in regex")
    exit()

open('/var/log/devices/lastlog_flapping.json', 'w').close() # clear
sleep(10) 


with open("/var/log/devices/lastlog_flapping.json", "r", errors='ignore') as log_file:
    for line in log_file:
        try:
            log_json = json.loads(line)
            ip = log_json["relayip"]
            hostname = log_json["hostname"]
            msg = log_json["message"]
            port, state = re.findall(r"LINKSTS (.*?) (UP|DOWN)", msg)[0]

            if(ip == last_ip and port == last_port):
                counter+= 1
                print(counter)

            if(counter == 5):

                lldp_port_capability = collect_command_output_lldp_port_capability(
                switch_user, switch_password, port, ip)

                if("Router" in str(lldp_port_capability) or "Bridge" in str(lldp_port_capability)):
                    process(ip, hostname, port, "UPLINK")
                elif(isUpLink(switch_user, switch_password, port, ip)):
                    process(ip, hostname, port, "UPLINK")

                else:
                    process(ip, hostname, port, "ACCESS")

                break

        except json.decoder.JSONDecodeError:
            print("File /var/log/devices/lastlog_flapping.json empty")
            exit()
        except IndexError:
            print("Index error in regex")
            exit()