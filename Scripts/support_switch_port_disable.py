#!/usr/local/bin/python3.7

from http.client import OK
import sys
import os
from support_tools_OmniSwitch import get_credentials, detect_port_loop, isUpLink, ssh_connectivity_check, debugging, add_new_save, check_save, send_file, collect_command_output_network_loop, script_has_run_recently
from time import strftime, localtime, sleep
import re  # Regex
from support_send_notification import send_message, send_message_request
from database_conf import *

# Script init
script_name = sys.argv[0]
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
            slot = 0
          # For each element, look if c/s/p is present. If yes,  we take the next element which is the port number
          # Log format OS6860E-VC-Building6 swlogd slNi MACMOVE DBG2: macCallBackProcessing_t[1174] [u:0][INS]: c/s/p: 1/1/14  d:vlan(1) MAC: 00:80:9f:57:df:33 vid:68 p:13 b:bridging t:learned e:0 dup:0 L3:0 cpu:0 mbi:0 McEntryNew:
        if " c\/s\/p:" in element:
            element_split = element.split()
            print(element_split)
            for i in range(len(element_split)):
                if element_split[i] == "c\\/s\\/p:":
                    port_a = element_split[i+1]
                    port = port_a.replace("\\", "", 2)
                    print(port)

function = "loop"
if script_has_run_recently(600,ipadd,function):
    print('you need to wait before you can run this again')
    os.system('logger -t montag -p user.info Executing script exit because executed within 5 minutes time period')
    exit()

# if check_timestamp()>15: # if the last log has been received less than 10 seconds ago :
if detect_port_loop():  # if there is more than 10 log with less of 2 seconds apart:
    print("call function disable port")
    subject = "A loop was detected on your OmniSwitch!"

    try:
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Port": port, "State": "Loop Detected"}, "fields": {"count": 1}}])
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
        info = "A loop has been detected on your network from the port {0} on device {1}.\nIf you click on Yes, the following action will be done: Port Admin Down".format(port, ipadd)
        answer = send_message_request(info, jid)

        if answer == "2":
            add_new_save(ipadd, port, "port_disable", choice="always")
            answer = '1'
        elif answer == "0":
            add_new_save(ipadd, port, "port_disable", choice="never")

        #if isUpLink(switch_user, switch_password, port, ipadd):
        #    answer = "0"
        #    info = "A loop has been detected on your network from the port {0} on device {1}. The port is detected as an Uplink, we do not proceed further".format(port, ipadd, ip_server)
        #    send_message(info,jid)

    elif save_resp == "-1":
        # Disable debugging logs "swlog appid bcmd subapp 3 level debug2"
        info = "Preventive Maintenance Application - A loop has been detected on your network from the port {0} on device {1}.\nDecision saved for this switch/port is set to Never, we do not proceed further".format(port, ipadd, ip_server)
        send_message(info,jid)
        appid = "slNi"
        subapp = "all"
        level = "info"
        # Call debugging function from support_tools_OmniSwitch
        print("call function enable debugging")
        debugging(switch_user, switch_password, ipadd, appid, subapp, level)
        try:
            write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Port": port, "State": "Debugging disabled"}, "fields": {"count": 1}}])
            sys.exit()
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            sys.exit()        
    else:
        answer = '1'
        info = "Preventive Maintenance Application - A loop has been detected on your network from the port {0} on device {1}.\nDecision saved for this switch/port is set to Always, we do proceed for disabling the interface".format(port, ipadd, ip_server)
        send_message(info,jid)

    if answer == '1':
        l_switch_cmd = []
#        l_switch_cmd.append("show  vlan members port " + port)
#        for switch_cmd in l_switch_cmd:
#            output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
#            if output != None:
#                output = str(output)
#                output_decode = bytes(output, "utf-8").decode("unicode_escape")
#                output_decode = output_decode.replace("', '","")
#                output_decode = output_decode.replace("']","")
#                output_vlan_members = output_decode.replace("['","")
#                print(output_vlan_members)
#                if re.search(r"ERROR", output_vlan_members):
#                    try:
#                        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Port": port, "State": "Port is UpLink - no port disabled"}, "fields": {"count": 1}}])
#                    except UnboundLocalError as error:
#                        print(error)
#                        sys.exit()
#                    except Exception as error:
#                        print(error)
#                        pass 
#                    info = "A loop has been detected on your network from the port {0} on device {1}. The port is detected as an Uplink, we do not proceed further".format(port, ipadd, ip_server)
#                    send_message(info,jid)
#                    sys.exit()
#                else:
                 ## if port is member of more than 2 VLAN tagged
#                    qtagged = re.findall(r"qtagged", output)
#                    if len(qtagged) > 1:
#                        try:
#                            write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Port": port, "State": "Port is UpLink - no port disabled"}, "fields": {"count": 1}}])
#                        except UnboundLocalError as error:
#                            print(error)
#                            sys.exit()
#                        except Exception as error:
#                            print(error)
#                            pass 
#                        info = "A loop has been detected on your network from the port {0} on device {1}. The port is detected as an Uplink, we do not proceed further".format(port, ipadd, ip_server)
#                        send_message(info,jid)
#                        sys.exit()
#                    else:
#                        pass   
        cmd = "interfaces port {0} admin-state disable".format(port)
        os.system('logger -t montag -p user.info Calling ssh_connectivity_check script')
        os.system('logger -t montag -p user.info SSH session for disabling port')
        ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
        try:
           write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Port": port, "State": "Loop Resolved"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
           print(error)
           sys.exit()
        except Exception as error:
           print(error)
           pass 
        # disable_port(switch_user,switch_password,ipadd,port)
        os.system('logger -t montag -p user.info Port disabled')
        filename_path, subject, action, result, category = collect_command_output_network_loop(switch_user, switch_password, ipadd, port)
        send_file(filename_path, subject, action, result, category, jid)
        sleep(5)
        # Disable debugging logs "swlog appid bcmd subapp 3 level debug2"
        appid = "slNi"
        subapp = "all"
        level = "info"
        # Call debugging function from support_tools_OmniSwitch
        print("call function enable debugging")
        os.system('logger -t montag -p user.info SSH session for disabling logs')
        debugging(switch_user, switch_password, ipadd, appid, subapp, level)
        # clear lastlog file
        sleep(10)
        open('/var/log/devices/lastlog_loop.json', 'w').close()
        try:
            write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Port": port, "State": "Debugging disabled"}, "fields": {"count": 1}}])
            sys.exit()
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            sys.exit()  
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
