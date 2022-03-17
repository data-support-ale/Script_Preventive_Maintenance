#!/usr/local/bin/python3.7

import sys
import os
import json
from time import strftime, localtime
from support_tools_OmniSwitch import get_credentials, send_file, collect_command_output_ovc, check_save, add_new_save, ssh_connectivity_check
from support_send_notification import send_message, send_message_request_advanced
from database_conf import *
import re

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

last = ""
with open("/var/log/devices/lastlog_ovc.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_ovc.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_ovc.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_ovc.json empty")
        exit()
    except IndexError:
        print("Index error in regex")
        exit()

    save_resp = check_save(ipadd, 0, "cloud_agent")
    # Sample log
    # OS6860E swlogd OPENVPN(168) Data: TCP: connect to [AF_INET]18.194.174.46:443 failed: S_errno_EHOSTUNREACH
    if "S_errno_EHOSTUNREACH" in msg:
        if save_resp == "-1":
            print("save response is never we exit script")
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "VPN": "Unknown", "Reason": "S_errno_EHOSTUNREACH"}, "fields": {"count": 1}}]) 
                sys.exit()       
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                sys.exit() 
        try:
            vpn_ip, reason = re.findall(r"\[AF_INET\](.*?):443 failed: (.*)", msg)[0]
            print(vpn_ip)
            print(reason)
            filename_path, subject, action, result, category = collect_command_output_ovc(switch_user, switch_password, vpn_ip, reason, host, ipadd)
            send_file(filename_path, subject, action, result, category)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "VPN": vpn_ip, "Reason": reason}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
               print(error)
               pass 
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
    # Sample log
    # OS6860E swlogd OPENVPN(168) Data: TCP: connect to [AF_INET]18.194.174.46:443 failed: S_errno_ETIMEDOUT
    elif "S_errno_ETIMEDOUT" in msg:
        if save_resp == "-1":
            print("save response is never we exit script")
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "VPN": "Unknown", "Reason": "S_errno_ETIMEDOUT"}, "fields": {"count": 1}}]) 
                sys.exit()       
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                sys.exit() 
        try:
            vpn_ip, reason = re.findall(r"[AF_INET](.*?):443 failed: (.*)", msg)[0]
            filename_path, subject, action, result, category = collect_command_output_ovc(switch_user, switch_password, vpn_ip, reason, host, ipadd)
            send_file(filename_path, subject, action, result, category)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "VPN": vpn_ip, "Reason": reason}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass 
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
    # Sample log
    # OS6860E swlogd openvpn[17911] RESOLVE: Cannot resolve host address: psza60a0ivu6v2.tenant.vpn.myovcloud.com:443 (Temporary failure in name resolution)
    elif "Cannot resolve host address" in msg:
        if save_resp == "-1":
            print("save response is never we exit script")
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "VPN": "Unknown", "Reason": "Cannot resolve host address"}, "fields": {"count": 1}}]) 
                sys.exit()       
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                sys.exit() 
        try:
            vpn_ip= re.findall(r"Cannot resolve host address: (.*?):443", msg)[0]
            reason = "Cannot resolve host address"
            filename_path, subject, action, result, category = collect_command_output_ovc(switch_user, switch_password, vpn_ip, reason, host, ipadd)
            send_file(filename_path, subject, action, result, category)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "VPN": vpn_ip, "Reason": reason}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass 
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
    # Sample log
    # OS6860E swlogd ovcCmm OVCloud ERR: ovcProcessCallHomeResponseSuccess: Invalid process status
    elif "Invalid process status" in msg:
        if save_resp == "-1":
            print("save response is never we exit script")
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "VPN": "Unknown", "Reason": "Invalid process status"}, "fields": {"count": 1}}]) 
                sys.exit()       
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                sys.exit() 
            
        try:
            reason = "Invalid process status"
            vpn_ip = "0"
            filename_path, subject, action, result, category = collect_command_output_ovc(switch_user, switch_password, vpn_ip, reason, host, ipadd)
            send_file(filename_path, subject, action, result, category)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "VPN": vpn_ip, "Reason": reason}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass 
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
    else:
        print("no pattern match - exiting script")
        sys.exit()

# always 1
#never -1
# ? 0
save_resp = check_save(ipadd, "0", "cloud_agent")

if save_resp == "0":
        if reason == "S_errno_EHOSTUNREACH" or reason == "S_errno_ETIMEDOUT":
            feature = "Restart Cloud-Agent"
            notif = "An OpenVPN issue is detected on OmniSwitch " + host + " reason: " + reason + ". Do you want to disable the Cloud-Agent on this switch? This command will result in device being disconnected from OV in cloud." + ip_server
            answer = send_message_request_advanced(notif, jid,feature)
            print(answer)
            if answer == "2":
                add_new_save(ipadd, "0", "cloud_agent", choice="always")
            elif answer == "0":
                add_new_save(ipadd, "0", "cloud_agent", choice="never")       
        else:
            feature = "Restart Cloud-Agent"
            notif = "A Cloud-Agent issue is detected on OmniSwitch " + host + " reason: " + reason + ". Do you want to disable the Cloud-Agent on this switch? This command will result in device being disconnected from OV in cloud. " + ip_server
            answer = send_message_request_advanced(notif, jid,feature)
            print(answer)
            if answer == "2":
                add_new_save(ipadd, "0", "cloud_agent", choice="always")
            elif answer == "0":
                add_new_save(ipadd, "0", "cloud_agent", choice="never")             
elif save_resp == "-1":
    try:
        print(vpn_ip)
        print(reason)
        print(ipadd)
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "VPN": vpn_ip, "Reason": reason}, "fields": {"count": 1}}])       
        sys.exit()   
    except UnboundLocalError as error:
       print(error)
       sys.exit()
    except Exception as error:
        print(error)
        sys.exit() 
        
elif save_resp == "1":
    answer = '2'
else:
    answer = '1'

if answer == '1':
    os.system('logger -t montag -p user.info Process terminated')
    # DISABLE Cloud-agent
    l_switch_cmd = []
    l_switch_cmd.append("cloud-agent admin-state disable")
    for switch_cmd in l_switch_cmd:
        ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
    info = "Cloud-Agent service is stopped on OmniSwitch: {}/{}".format(host,ipadd)
    send_message(info, jid)        

elif answer == '2':
    os.system('logger -t montag -p user.info Process terminated')
    # DISABLE Cloud-agent
    l_switch_cmd = []
    l_switch_cmd.append("cloud-agent admin-state disable")
    for switch_cmd in l_switch_cmd:
        ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)

## Value 3 when we return advanced value we reload the Cloud-Agent
elif answer == '3':
    os.system('logger -t montag -p user.info Process terminated')
    # Cloud-agent restart
    cmd = "cloud-agent admin-state restart"
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
    info = "Cloud-Agent is restarted on OmniSwitch: {}/{}".format(host,ipadd)
    send_message(info, jid)

else:
    print("Mail request set as no")
    os.system('logger -t montag -p user.info Mail request set as no')

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "VPN": vpn_ip, "Reason": reason}, "fields": {"count": 1}}]) 
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    sys.exit()     