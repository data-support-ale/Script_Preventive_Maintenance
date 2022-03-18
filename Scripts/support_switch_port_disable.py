#!/usr/local/bin/python3.7

import sys
import os
from support_tools_OmniSwitch import get_credentials, detect_port_loop, isUpLink, ssh_connectivity_check, debugging, add_new_save, check_save, send_file, collect_command_output_network_loop, script_has_run_recently
from time import strftime, localtime, sleep
#import re  # Regex
from support_send_notification import send_message, send_message_request
from database_conf import *

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

content_variable = open('/var/log/devices/lastlog_loop.json', 'r')
file_lines = content_variable.readlines()
content_variable.close()

if len(file_lines) != 0:
    last_line = file_lines[0]
    f = last_line.split(',')
    # For each element, look if relayip is present. If yes,  separate the text and the ip address
    for element in f:
        if "relayip" in element:
            element_split = element.split(':')
            ipadd_quot = element_split[1]
            # delete quotations
            ipadd = ipadd_quot[-len(ipadd_quot)+1:-1]
            print(ipadd)
            port = 0
          # For each element, look if port is present. If yes,  we take the next element which is the port number
        if "port" in element:
            element_split = element.split()
            print(element_split)
            for i in range(len(element_split)):
                if element_split[i] == "port":
                    port = element_split[i+1]
                    n = len(str(port))
                    print(n)
                    dig = []
                    dig = list(int(port) for port in str(port))
                    if n > 2:
                        print("wrong port ID")
                        # clear lastlog file
                        open('/var/log/devices/lastlog_loop.json', 'w').close()
                        sys.exit()
                    slot = element_split[i+3]
                    if slot == "0":
                        slot = "1"
                    elif slot == "4":
                        slot == "2"
                    elif slot == "8":
                        slot == "3"
                    elif slot == "12":
                        slot == "4"
                    else:
                        slot == "5"
            # looking for chassis ID number:
                    # modify the format of the port number to suit the switch interface
                    port = "{0}/1/{1}".format(slot, port)

function = "loop"
if script_has_run_recently(300,ipadd,function):
    print('you need to wait before you can run this again')
    os.system('logger -t montag -p user.info Executing script exit because executed within 5 minutes time period')
    exit()

# if check_timestamp()>15: # if the last log has been received less than 10 seconds ago :
if detect_port_loop():  # if there is more than 10 log with less of 2 seconds apart:
    print("call function disable port")
    subject = "A loop was detected on your OmniSwitch!"

    try:
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(
            __file__)), "tags": {"IP": ipadd, "Port": port}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 

    # always 1
    #never -1
    # ? 0
    save_resp = check_save(ipadd, port, "port_disable")

    if save_resp == "0":
        info = "A loop has been detected on your network from the port {0} on device {1}. (if you click on Yes, the following action will be done: Port Admin Down - Server: {2})".format(
            port, ipadd, ip_server)
        answer = send_message_request(info, jid)

        if isUpLink(port, ipadd):
            answer = "0"
            info = "A loop has been detected on your network from the port {0} on device {1}. The port is detected as an Uplink, we do not proceed further".format(port, ipadd, ip_server)
            send_message(info,jid)

        if answer == "2":
            add_new_save(ipadd, port, "port_disable", choice="always")
            answer = '1'
        elif answer == "0":
            add_new_save(ipadd, port, "port_disable", choice="never")
    elif save_resp == "-1":
        # Disable debugging logs "swlog appid bcmd subapp 3 level debug2"
        info = "A loop has been detected on your network from the port {0} on device {1}. Decision saved for this switch/port is set to Never, we do not proceed further".format(port, ipadd, ip_server)
        send_message(info,jid)
        appid = "bcmd"
        subapp = "all"
        level = "info"
        # Call debugging function from support_tools_OmniSwitch
        print("call function enable debugging")
        debugging(switch_user, switch_password, ipadd, appid, subapp, level)
        try:
            write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Port": port}, "fields": {"count": 1}}])
            sys.exit()
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            sys.exit()        
    else:
        answer = '1'
        info = "A loop has been detected on your network from the port {0} on device {1}. Decision saved for this switch/port is set to Always, we do proceed for disabling the interface".format(port, ipadd, ip_server)
        send_message(info,jid)

    if answer == '1':
        cmd = "interfaces port {0} admin-state disable".format(port)
        os.system('logger -t montag -p user.info Calling ssh_connectivity_check script')
        os.system('logger -t montag -p user.info SSH session for disabling port')
        ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
        # disable_port(switch_user,switch_password,ipadd,port)
        os.system('logger -t montag -p user.info Port disabled')
        if jid != '':
            info = "A loop has been detected on your network and the port {0} is administratively disabled on device {1}".format(
                port, ipadd)
            filename_path, subject, action, result, category = collect_command_output_network_loop(switch_user, switch_password, ipadd, port)
            send_file(filename_path, subject, action, result, category)
        sleep(5)
        # Disable debugging logs "swlog appid bcmd subapp 3 level debug2"
        appid = "bcmd"
        subapp = "all"
        level = "info"
        # Call debugging function from support_tools_OmniSwitch
        print("call function enable debugging")
        os.system('logger -t montag -p user.info SSH session for disabling logs')
        debugging(switch_user, switch_password, ipadd, appid, subapp, level)
        # clear lastlog file
        sleep(10)
        open('/var/log/devices/lastlog_loop.json', 'w').close()
    else:
        print("Mail request set as no")
        os.system('logger -t montag -p user.info Mail request set as no')
        sleep(1)
        open('/var/log/devices/lastlog_loop.json', 'w').close()

else:
    print("logs are too close")
    os.system('logger -t montag -p user.info Logs are too close')
    # clear lastlog file
    open('/var/log/devices/lastlog_loop.json', 'w').close()
