#!/usr/local/bin/python3.7

import sys
import os
#import getopt
import json
#import logging
#import subprocess
from time import strftime, localtime
#import requests
#import datetime
import re
from support_tools_OmniSwitch import get_credentials
from support_send_notification import send_message, send_alert
#from support_OV_get_wlan import OvHandler
from database_conf import *
#import psutil
#print(psutil.cpu_percent())

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()


def deassociation(ipadd, device_mac, reason, reason_number):
    message = "WLAN Deassociation detected reason : {0} from Stellar AP {1}, client MAC Address {2}".format(
        reason, ipadd, device_mac)
    message_bis = "WLAN Deassociation detected reason : {0} from Stellar AP {1}".format(
        reason_number, ipadd)
    os.system('logger -t montag -p user.info ' + message_bis)
    subject_content = "[TS LAB] A deassociation is detected on Stellar AP!"
    message_content_1 = "WLAN Alert - There is a WLAN deassociation detected on server {0} from Stellar AP {1}, Device's MAC Address: {2} .".format(
        ip_server, ipadd, device_mac)
    print(message_content_1)
    message_content_2 = "Reason number: ".format(reason_number)
    send_alert(message, jid)
    send_message(message_reason, jid)
    try:
        write_api.write(bucket, org, [{"measurement": "support_wlan_deassociation", "tags": {"AP_IPAddr": ipadd, "Client_MAC": device_mac, "Reason_Deassociation": reason, "topic": "deauth"}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 

    # REST-API for login on OV
    #ovrest = OvHandler()

    # REST-API for getting WLAN information from OV Wireless List
    #channel, clientName = ovrest.postWLANClient(device_mac)
    #category = ovrest.postWLANIoT(device_mac)

    # If client does not exist on OV WLAN Client list
    # if clientName != None:
    #   info =  "The client {0} MAC Address: {1} is associated to Radio Channel: {2}".format(clientName,device_mac,channel)
    # send_message(info,jid)
    # if category != None:
    #   info =  "This client device category is: {0}".format(category)
    # send_message(info,jid)


def reboot(ipadd):
    os.system('logger -t montag -p user.info reboot detected')
    subject_content = "[TS LAB] A reboot is detected on Stellar AP!"
    message_content_1 = "WLAN Alert - There is a Stellar reboot detected on server {0} from Stellar AP {1}".format(
        ip_server, ipadd)
    message_content_2 = "sysreboot"
    send_alert(message_content_1, jid)
    send_message(message_reason, jid)
    try:
        write_api.write(bucket, org, [{"measurement": "support_wlan_ap_reboot", "tags": {"AP_IPAddr": ipadd, "Reason": "sysreboot"}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 

def unexpected_reboot(ipadd):
    os.system('logger -t montag -p user.info reboot detected')
    subject_content = "[TS LAB] A reboot is detected on Stellar AP!"
    message_content_1 = "WLAN Alert - There is a Stellar unexpected reboot detected on server {0} from Stellar AP {1} - please check the LANPOWER is running fine on OmniSwitch and verify the capacitor-detection is disabled".format(
        ip_server, ipadd)
    message_content_2 = "sysreboot"
    send_alert(message_content_1, jid)
    send_message(message_reason, jid)
    try:
        write_api.write(bucket, org, [{"measurement": "support_wlan_ap_reboot", "tags": {"AP_IPAddr": ipadd, "Reason": "unexpected_reboot"}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 

def upgrade(ipadd):
    os.system('logger -t montag -p user.info upgrade detected')
    subject_content = "[TS LAB] An upgrade is detected on Stellar AP!"
    message_content_1 = "WLAN Alert - There is a Stellar upgrade detected on server {0} from Stellar AP {1}".format(
        ip_server, ipadd)
    message_content_2 = "sysupgrade"
    send_alert(message_content_1, jid)
    send_message(message_reason, jid)
    try:
        write_api.write(bucket, org, [{"measurement": "support_wlan_ap_reboot", "tags": {"AP_IPAddr": ipadd, "Reason": "sysupgrade"}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 

def exception(ipadd):
    os.system('logger -t montag -p user.info exception detected')
    subject_content = "[TS LAB] An exception (Fatal exception, Exception stack, Kernel Panic) is detected on Stellar AP!"
    message_content_1 = "WLAN Alert - There is a Stellar exception detected on server {0} from Stellar AP {1}".format(
        ip_server, ipadd)
    message_content_2 = "Exception"
    send_alert(message_content_1, jid)
    send_message(message_reason, jid)
    try:
        write_api.write(bucket, org, [{"measurement": "support_wlan_ap_reboot", "tags": {"AP_IPAddr": ipadd, "Reason": "exception"}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 

def internal_error(ipadd):
    os.system('logger -t montag -p user.info internal error detected')
    subject_content = "[TS LAB] An Internal Error is detected on Stellar AP!"
    message_content_1 = "WLAN Alert - There is an Internal Error detected on server {0} from Stellar AP {1}".format(
        ip_server, ipadd)
    message_content_2 = "Internal Error"
    send_alert(message_content_1, jid)
    send_message(message_reason, jid)
    try:
        write_api.write(bucket, org, [{"measurement": "support_wlan_ap_reboot", "tags": {"AP_IPAddr": ipadd, "Reason": "internal error"}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 

def target_asserted(ipadd):
    os.system('logger -t montag -p user.info target asserted detected')
    subject_content = "[TS LAB] A Target Asserted Error is detected on Stellar AP!"
    message_content_1 = "WLAN Alert - There is a Target Asserted error detected on server {0} from Stellar AP {1}".format(
        ip_server, ipadd)
    message_content_2 = "Target Asserted"
    send_alert(message_content_1, jid)
    send_message(message_reason, jid)
    try:
        write_api.write(bucket, org, [{"measurement": "support_wlan_ap_reboot", "tags": {"AP_IPAddr": ipadd, "Reason": "target asserted"}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 


def kernel_panic(ipadd):
    os.system('logger -t montag -p user.info Kernel Panic detected')
    subject_content = "[TS LAB] A Kernel Panic is detected on Stellar AP!"
    message_content_1 = "WLAN Alert - There is a Kernel Panic error detected on server {0} from Stellar AP {1}".format(
        ip_server, ipadd)
    message_content_2 = "Kernel panic"
    send_alert(message_content_1, jid)
    send_message(message_reason, jid)
    try:
        write_api.write(bucket, org, [{"measurement": "support_wlan_ap_reboot", "tags": {"AP_IPAddr": ipadd, "Reason": "kernel panic"}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 


def limit_reached(ipadd):
    os.system('logger -t montag -p user.info Associated STA Limit Reached!')
    subject_content = "[TS LAB] Associated STA Limit Reached!"
    message_content_1 = "WLAN Alert - The Stellar AP {0} has reached the limit of WLAN Client association!".format(
        ipadd)
    message_content_2 = "Associated STA limit reached"
    send_alert(message_content_1, jid)
    send_message(message_reason, jid)
    try:
        write_api.write(bucket, org, [{"measurement": "support_wlan_ap_reboot", "tags": {"AP_IPAddr": ipadd, "Reason": "STA limit reached"}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 

def authentication_step1(ipadd, device_mac, auth_type, ssid, deassociation):
    try:
        write_api.write(bucket, org, [{"measurement": "support_wlan_association", "tags": {"AP_IPAddr": ipadd, "Client_MAC": device_mac, "Auth_type": auth_type, "Association": deassociation}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 
    if "0" in deassociation:
        message = "[{0}] WLAN deassociation detected from client {1} on Stellar AP {2} with Authentication type {3}".format(
            ssid, device_mac, ipadd, auth_type)
        os.system('logger -t montag -p user.info ' + message)


def authentication_step2(ipadd, user_name, ssid):
    try:
        write_api.write(bucket, org, [{"measurement": "support_wlan_association", "tags": {"AP_IPAddr": ipadd, "Client_MAC": device_mac, "User name": user_name}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 
    message = "[{0}] WLAN authentication on Captive Portal from User: {1} on Stellar AP {2}".format(
        ssid, user_name, ipadd)
    os.system('logger -t montag -p user.info ' + message)


def mac_authentication(device_mac_auth, ARP, source, reason):
    try:
        write_api.write(bucket, org, [{"measurement": "support_wlan_mac_auth", "tags": {"Client_MAC": device_mac_auth, "ARP": ARP, "Source": source, "Reason": reason}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 
    if "failed" in reason:
        message = "WLAN Authentication failed from client {0} assigned to {1} from {2}".format(
            device_mac_auth, ARP, source)
        os.system('logger -t montag -p user.info ' + message)
    elif "will" in reason:
        message = "WLAN Authentication success from client {0} assigned to {1} from {2}".format(
            device_mac_auth, ARP, source)
        os.system('logger -t montag -p user.info ' + message)
    else:
        message = "WLAN Authentication success from client {0} assigned to {1} from {2} - reason: {3}".format(
            device_mac_auth, ARP, source, reason)
        os.system('logger -t montag -p user.info ' + message)


def radius_authentication(auth_result, device_mac, accounting_status):
    try:
        write_api.write(bucket, org, [{"measurement": "support_wlan_radius_auth", "tags": {"Client_MAC": device_mac, "Auth_Result": auth_result, "Accounting_status": accounting_status}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 
    if "Failed" in auth_result:
        message = "WLAN 802.1x Authentication {0} for client {1}".format(
            auth_result, device_mac)
        os.system('logger -t montag -p user.info ' + message)
    if "Success" in auth_result:
        message = "WLAN 802.1x Authentication {0} for client {1}".format(
            auth_result, device_mac)
        os.system('logger -t montag -p user.info ' + message)
    if "null" in auth_result:
        os.system(
            'logger -t montag -p user.info Radius authentication attempt or in progress')
    else:
        message = "WLAN 8021x Accounting {0} for {1}".format(
            accounting_status, device_mac)
        os.system('logger -t montag -p user.info ' + message)


def dhcp_ack(ipadd, device_mac):
    try:
        write_api.write(bucket, org, [{"measurement": "support_wlan_dhcp", "tags": {"Client_MAC": device_mac, "DHCP_Lease": ip_dhcp}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 
    message = "DHCP Ack received with IP Address {0} for client {1}".format(
        ip_dhcp, device_mac)
    os.system('logger -t montag -p user.info ' + message)


def extract_reason():
    last = ""
    reason = device_mac = ap_mac = 0
    with open("/var/log/devices/lastlog_deauth.json", "r", errors='ignore') as log_file:
        for line in log_file:
            last = line

    with open("/var/log/devices/lastlog_deauth.json", "w", errors='ignore') as log_file:
        log_file.write(last)

    with open("/var/log/devices/lastlog_deauth.json", "r", errors='ignore') as log_file:
        log_json = json.load(log_file)
        msg = log_json["message"]
        f = msg.split(',')
        for element in f:
            if "reason" in element:
                reason = re.findall(r"reason (.*)", msg)[0]
                reason_number = re.findall(r"reason (.*?)\(", msg)[0]
                reason = str(reason)
                device_mac = re.findall(
                    r".*\[(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\].*", msg)[0]
                ap_mac = re.findall(
                    r".*\((([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\).*", msg)[0]
                device_mac = str(device_mac[0])
                ap_mac = str(ap_mac[0])
                print("WLAN Deauthentication use case")
                print(reason)
                print(device_mac)
                print(ap_mac)
    return reason, device_mac, reason_number


def extract_ipadd():
    last = ""
    with open("/var/log/devices/lastlog_deauth.json", "r", errors='ignore') as log_file:
        for line in log_file:
            last = line

    with open("/var/log/devices/lastlog_deauth.json", "w", errors='ignore') as log_file:
        log_file.write(last)

    with open("/var/log/devices/lastlog_deauth.json", "r", errors='ignore') as log_file:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        message_reason = log_json["message"]
        ipadd = str(ipadd)
        print(ipadd)
        l = []
        l.append('/code ')
        l.append(message_reason)
        message_reason = ''.join(l)
    return ipadd, message_reason


def radius_failover():
    # open the file lastlog_8021X_authentication.json  and the Radius Authentication Server reachability
    pattern_Device_MAC = re.compile(
        '.*\<(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\>.*')
    content_variable = open(
        '/var/log/devices/lastlog_8021X_authentication.json', 'r')
    file_lines = content_variable.readlines()
    content_variable.close()
    last_line = file_lines[-1]
    f = last_line.split(',')
    for element in f:
        if "RADIUS" in element:
            # In case of too many failed retransmit attempts, Radius Server is considered as unreachable
            if "too many failed retransmit attempts" in element:
                os.system(
                    'logger -t montag -p user.info Radius Server unreachable - too many failed retransmit attempts')
            if "No response from Authentication server" in element:
                os.system(
                    'logger -t montag -p user.info Primary Radius Server unreachable')
            if "failover" in element:
                os.system(
                    'logger -t montag -p user.info Failover to backup server')
                element_split = element.split(' ')
                for i in range(len(element_split)):
                    if element_split[i] == "server":
                        print("802.1x Authentication server unreachable")
                        server = element_split[i+1]
                        os.system(
                            'logger -t montag -p user.info Radius Server unreachable ' + server)
# Condition hardcoded to review once we have additionnal syslog messages in AWOS 4.0.4
            if "RADIUS Authentication server 10.130.7.25" in element:
                os.system(
                    'logger -t montag -p user.info Authentication sent to Backup Radius Server 10.130.7.25')


def extract_RADIUS():
    last = ""
    with open("/var/log/devices/lastlog_8021X_authentication.json", "r", errors='ignore') as log_file:
        for line in log_file:
            last = line

    with open("/var/log/devices/lastlog_8021X_authentication.json", "w", errors='ignore') as log_file:
        log_file.write(last)

    with open("/var/log/devices/lastlog_8021X_authentication.json", "r", errors='ignore') as log_file:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
        auth_result = "null"
        device_8021x_auth = accounting_status = "null"
        f = msg.split(',')
        for element in f:
            print(element)
            if "RADIUS" in element:
                if "RADIUS packet send to" in element:
                    element_split = element.split(' ')
                    for i in range(len(element_split)):
                        if element_split[i] == "to":
                            server = element_split[i+1]
                            server = server.replace("\"", "")
                            os.system(
                                'logger -t montag -p user.info Authentication sent to Radius Server ' + server)
            if "8021x Authentication" in element:
                auth_result, device_8021x_auth = re.findall(
                    r"8021x-Auth (.*?) for Sta<(.*?)>", msg)[0]
                print("Authentication success use case")
                # Wireless roam_trace[10065] <INFO> [AP DC:08:56:54:2D:40@10.130.7.76] [Employee_EAP @ ath11]: 8021x Authentication Success for Sta<de:ab:50:25:b8:71>
            if "8021x-Auth Failed" in element:
                auth_result = "Failed"
                device_8021x_auth = re.findall(r"STA <(.*?)>", msg)[0]
                print("Authentication failure use case")
                # Wireless roam_trace[10065] <INFO> [AP DC:08:56:54:2D:40@10.130.7.76] [Employee_EAP @ ath11]: 8021x-Auth Failed, STA <de:ab:50:25:b8:71> Disconnect
            if "8021x-Auth Accounting" in element:
                accounting_status, device_8021x_auth = re.findall(
                    r"8021x-Auth Accounting (.*?) for STA <(.*?)>", msg)[0]
                auth_result = "0"
                print("accounting use case")
                # Wireless roam_trace[10065] <INFO> [AP DC:08:56:54:2D:40@10.130.7.76] [Employee_EAP @ ath11]: 8021x-Auth Accounting start for STA <de:ab:50:25:b8:71>
            print(auth_result)
            print(device_8021x_auth)
            print(accounting_status)
    return auth_result, device_8021x_auth, accounting_status


def extract_WCF():
    pattern_Device_MAC = re.compile(
        '.*\[(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\].*')
    pattern_FQDN = re.compile('(fqdn:\[(.*?)\])')
    pattern_domain = re.compile('(domain:\[(.*?)\])')
    content_variable = open('/var/log/devices/lastlog_wcf.json', 'r')
    file_lines = content_variable.readlines()
    content_variable.close()
    last_line = file_lines[-1]
    f = last_line.split(',')
    # Variables initialized to null
    domain = device_mac_wcf = fqdn = "null"
    print("Extract WCF function")
    for element in f:
        if "Add dns domain" in element:
            domain = re.search(pattern_domain, str(f)).group(1)
            print(domain)
            message = "{0} added in AP cache".format(domain)
            os.system('logger -t montag -p user.info  ' + message)
        if "<ALERT>" in element:
            device_mac_wcf = re.search(pattern_Device_MAC, str(f)).group(1)
            fqdn = re.search(pattern_FQDN, str(f)).group(1)
            print("WCF Block FQDN: " + fqdn)
            message = "Web Content Filtering for device {0} when accessing Site {1}".format(
                device_mac_wcf, fqdn)
            os.system('logger -t montag -p user.info  ' + message)
            try:
                write_api.write(bucket, org, [{"measurement": "support_wlan_wcf", "tags": {"Client_MAC": device_mac_wcf, "URL": fqdn}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass 

def extract_ARP():
    # open the file lastlog_mac_authentication.json  and and get the Access Role Profile + result + source
    pattern_Device_MAC = re.compile(
        '.*\<(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\>.*')
    content_variable = open(
        '/var/log/devices/lastlog_mac_authentication.json', 'r')
    file_lines = content_variable.readlines()
    content_variable.close()
    last_line = file_lines[-1]
    f = last_line.split(',')
    # Variables initialized to null
    device_mac_auth = ARP = source = reason = "null"
    for element in f:
        if "enforcement" in element or "updated" in element:
            # Variables initialized to default values
            source = "IoT"
            reason = "Enforcement"
            device_mac_auth = re.search(pattern_Device_MAC, str(f)).group(1)
            element_split = element.split(' ')
            for i in range(len(element_split)):
                if element_split[i] == "Role":
                    print("Access Role assigned")
                    ARP = element_split[i+1]
                    ARP = ARP.replace("(", " ", 2).replace(")", " ", 2)

        elif "Access Role" in element:
            device_mac_auth = re.search(pattern_Device_MAC, str(f)).group(1)
            element_split = element.split(' ')
            for i in range(len(element_split)):
                if element_split[i] == "Access":
                    print("Access Role assigned")
                    ARP = element_split[i+1]
                    ARP = ARP.replace("(", " ", 2).replace(")", " ", 2)

                elif element_split[i] == "Role":
                    print("Access Role assigned")
                    ARP = element_split[i+1]
                    ARP = ARP.replace("(", " ", 2).replace(")", " ", 2)

                if element_split[i] == "from":
                    source = element_split[i+1]
                    source = source.replace("(", " ", 2).replace(")", " ", 2)
                    if element_split[i+2] == "(MAC-Auth":
                        reason = element_split[i+2] + " " + element_split[i+3]
                        reason = reason.replace(
                            "(", " ", 2).replace(")", " ", 2)

                    else:
                        reason = element_split[i+2]
                        reason = reason.replace(
                            "(", " ", 2).replace(")", " ", 2)
    return ARP, device_mac_auth, source, reason


def extract_Policy():
    # open the file lastlog_policy.json and get the Policy List assigned to client + Location Policy/Period check
    content_variable = open('/var/log/devices/lastlog_policy.json', 'r')
    file_lines = content_variable.readlines()
    content_variable.close()
    last_line = file_lines[-1]
    f = last_line.split(',')
    # Variables initialized to null
    Policy = "null"
    for element in f:
        if "PolicyList" in element:
            element_split = element.split(' ')
            for i in range(len(element_split)):
                if element_split[i] == "PolicyList":
                    print("Policy assigned")
                    Policy = element_split[i+3]
                    Policy = Policy.replace("[", " ", 2).replace(
                        "]", " ", 2).replace("\"", " ", 2)
                    os.system(
                        'logger -t montag -p user.info Policy List applied: ' + Policy)
    ### If Location Policy check fails ####
    # Log sample [SSID-TEST-EGE @ ath01]: Loaction Policy [__SSID-TEST-EGE] check Failed, STA <00:1e:2a:c8:2f:e4> Disconnect
        if "check Failed" in element:
            try:
                pattern_Device_MAC = re.compile('.*\<(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\>.*')
                device_mac = re.search(pattern_Device_MAC, str(f)).group(1)
                print(device_mac)
            except IndexError:
                print("Index error in regex")
                sys.exit()
            os.system('logger -t montag -p user.info Access to SSID not authorized as per Location Policy')
            try:
                info = "Access to SSID not authorized as per Location Policy"
                send_message(info,jid)
                write_api.write(bucket, org, [{"measurement": "support_wlan_policy", "tags": {"Client_MAC": device_mac, "Reason": "Rejected by Location Policy"}, "fields": {"count": 1}}])
                sys.exit()
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass 
    ### If Location Period check fails ####
    # Log sample [SSID-TEST-EGE @ ath01]: check period policy ddddddedzdzedzedz, current time is not allowed to access, STA <00:1e:2a:c8:2f:e4> Disconect
        if "current time is not allowed to access" in element:
            try:
                pattern_Device_MAC = re.compile('.*\<(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\>.*')
                device_mac = re.search(pattern_Device_MAC, str(f)).group(1)
                print(device_mac)
            except IndexError:
                print("Index error in regex")
                sys.exit()
            os.system('logger -t montag -p user.info Access to SSID not authorized as per Period Policy')
            try:
                info = "Access to SSID not authorized as per Period Policy"
                send_message(info,jid)
                write_api.write(bucket, org, [{"measurement": "support_wlan_policy", "tags": {"Client_MAC": device_mac, "Reason": "Rejected by Period Policy"}, "fields": {"count": 1}}])
                sys.exit()
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass 
    ### If Can't Match Access Policy ####
    # Log sample [PORTAL CNP @ ath15]: MAC Authentication Reject for STA <7c:d6:61:b2:f9:43>, reply message is Can't Match Access Policy
        if "Can't Match Access Policy" in element:
            try:
                pattern_Device_MAC = re.compile('.*\<(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\>.*')
                device_mac = re.search(pattern_Device_MAC, str(f)).group(1)
                print(device_mac)
            except IndexError:
                print("Index error in regex")
                sys.exit()
            os.system('logger -t montag -p user.info Access to SSID not authorized as no UPAM access policy match')
            try:
                info = "Access to SSID not authorized as there is no Access Policy matching with Radius Access-Request"
                send_message(info,jid)
                write_api.write(bucket, org, [{"measurement": "support_wlan_policy", "tags": {"Client_MAC": device_mac, "Reason": "Rejected by Can't Match Access Policy"}, "fields": {"count": 1}}])
                sys.exit()
            except UnboundLocalError as error:
                print(error)
                sys.exit()    
            except Exception as error:
                print(error)
                pass 
    return Policy


def extract_ip_dhcp():
    # open the file lastlog_dhcp.json  and check if the DHCPACK with DHCP Lease is received
    content_variable = open('/var/log/devices/lastlog_dhcp.json', 'r')
    file_lines = content_variable.readlines()
    content_variable.close()
    last_line = file_lines[-1]
    f = last_line.split(',')
    # Variables initialized to null
    ip_dhcp = "null"
    for element in f:
        if "DHCPACK" or "dhcp ack" in element:
            element_split = element.split(' ')
            for i in range(len(element_split)):
                if element_split[i] == "address":
                    print("DHCP Lease received")
                    ip_dhcp = element_split[i+1]
                    ip_dhcp = ip_dhcp.strip(" \"\\")
    return ip_dhcp


def extract_ip_port():
    # open the file lastlog_wlan_authentication.json  and get the AP IP Address + Client MAC Address + Authentication type + SSID
    pattern_AP_MAC = re.compile(
        '.*\((([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\).*')
    pattern_Device_MAC = re.compile(
        '.*\[(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\].*')
    content_variable = open(
        '/var/log/devices/lastlog_wlan_authentication.json', 'r')
    file_lines = content_variable.readlines()
    content_variable.close()
    last_line = file_lines[-1]
    f = last_line.split(',')
    # For each element, look if relayip is present. If yes,  separate the text and the ip address
    for element in f:
        if "relayip" in element:
            element_split = element.split(':')
            ipadd_quot = element_split[1]
            ipadd = ipadd_quot[-len(ipadd_quot)+1:-1]
    # Variables initialized to null
            device_mac = ap_mac = reason = auth_type = user_name = ssid = deassociation = "null"
        # For each element, look if reason is present, if yes, we take the AP MAC Address and the Device MAC Address
        if "SSID" in element:
            print("SSID in element")
            element_split = element.split()
            for i in range(len(element_split)):
                if element_split[i] == "SSID":
                    ssid = element_split[i+2]
                    ssid = ssid.strip(" []")
                    print(ssid)

        if "AuthType" in element:
            print("AuthType in element")
            device_mac = re.search(pattern_Device_MAC, str(f)).group(1)
            element_split = element.split()
            for i in range(len(element_split)):
                if element_split[i] == "AuthType":
                    auth_type = element_split[i+1]
                    auth_type = auth_type.strip(" ()")
                    auth_type = auth_type.replace("}", "]", 1)

        if "status" in element:
            print("Association status in element")
            device_mac = re.search(pattern_Device_MAC, str(f)).group(1)
            element_split = element.split()
            for i in range(len(element_split)):
                if element_split[i] == "status":
                    deassociation = element_split[i+1]
                    deassociation = deassociation.strip(" []")

        if "Portalname" in element:
            device_mac = re.search(pattern_Device_MAC, str(f)).group(1)
            element_split = element.split()
            for i in range(len(element_split)):
                if element_split[i] == "Portalname":
                    user_name = element_split[i+1]
                    user_name = user_name.replace("(", " ", 1)
    return ipadd, device_mac, ap_mac, auth_type, user_name, ssid, deassociation


def extract_WIPS():
    last = ""
    device_mac = reason = 0
    with open("/var/log/devices/lastlog_wips.json", "r", errors='ignore') as log_file:
        for line in log_file:
            last = line

    with open("/var/log/devices/lastlog_wips.json", "w", errors='ignore') as log_file:
        log_file.write(last)

    with open("/var/log/devices/lastlog_wips.json", "r", errors='ignore') as log_file:
        log_json = json.load(log_file)
        msg = log_json["message"]
        f = msg.split(',')
        for element in f:
            if "Add black list" in element:
                device_mac = re.findall(
                    r"Add black list mac is (.*?) ]", msg)[0]
                print(device_mac)
                message = "WLAN WIPS - Adding Client's MAC Address {0} in the Block List".format(
                    device_mac)
                os.system('logger -t montag -p user.info  ' + message)
                send_alert(message, jid)
                try:
                   write_api.write(bucket, org, [{"measurement": "support_wlan_wips", "tags": {"Client_MAC": device_mac, "Reason": "Added in BlockList"}, "fields": {"count": 1}}])
                except UnboundLocalError as error:
                   print(error)
                   sys.exit()
                except Exception as error:
                   print(error)
                   pass 
            if "status 37" in element:
                device_mac = re.findall(
                    r".*\[(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\].*", msg)[0]
                device_mac = str(device_mac[0])
                reason = re.findall(r"status (.*?),", msg)[0]
                print(reason)
                print(device_mac)
                message = "WLAN Client MAC Address {0} authentication rejected by ACL".format(
                    device_mac)
                os.system('logger -t montag -p user.info  ' + message)
                send_alert(message, jid)
                try:
                   write_api.write(bucket, org, [{"measurement": "support_wlan_wips", "tags": {"Client_MAC": device_mac, "Reason": reason}, "fields": {"count": 1}}])
                except UnboundLocalError as error:
                   print(error)
                   sys.exit()
                except Exception as error:
                   print(error)
                   pass 
    return device_mac, reason


## if $msg contains 'Recv the  wam module  notify  data user'##
if sys.argv[1] == "auth_step1":
    print("call function authentication step1")
    os.system(
        'logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
    ipadd, device_mac, ap_mac, auth_type, user_name, ssid, deassociation = extract_ip_port()
    authentication_step1(ipadd, device_mac, auth_type, ssid, deassociation)
    sys.exit(0)

## if $msg contains ':authorize' or $msg contains 'from MAC-Auth' or $msg contains 'Access Role'##
##    if $msg contains 'Access Role(' ##
elif sys.argv[1] == "mac_auth":
    print("call function mac_authentication")
    os.system(
        'logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
    arp, device_mac_auth, source, reason = extract_ARP()
    mac_authentication(device_mac_auth, arp, source, reason)
    sys.exit(0)

## if $msg contains '8021x-Auth' or $msg contains 'RADIUS' or $msg contains '8021x Authentication' ##
elif sys.argv[1] == "8021X":
    print("call function radius_authentication")
    os.system(
        'logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
    auth_result, device_8021x_auth, accounting_status = extract_RADIUS()
    radius_authentication(auth_result, device_8021x_auth, accounting_status)
    sys.exit(0)

# if $msg contains 'too many failed retransmit attempts' or $msg contains 'No response'
elif sys.argv[1] == "failover":
    print("call function radius_failover")
    os.system(
        'logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
    radius_failover()
    sys.exit(0)

## if $msg contains ':authorize' or $msg contains 'from MAC-Auth' or $msg contains 'Access Role'##
##     if $msg contains 'Get PolicyList' ##
## OR if $msg contains 'check period policy' or $msg contains 'Loaction Policy' ##
elif sys.argv[1] == "policy":
    print("call function policy")
    os.system(
        'logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
    extract_Policy()
    sys.exit(0)


## if $msg contains 'Found DHCPACK for STA'  or $msg contains 'Found dhcp ack for STA'##
elif sys.argv[1] == "dhcp":
    print("call function dhcp_ack")
    os.system(
        'logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
    ipadd, device_mac, ap_mac, auth_type, user_name, ssid, deassociation = extract_ip_port()
    ip_dhcp = extract_ip_dhcp()
    dhcp_ack(ipadd, device_mac)
    sys.exit(0)

## if $msg contains 'verdict:[NF_DROP]' #
elif sys.argv[1] == "wcf_block":
    print("call function wcf_block")
    os.system(
        'logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
    extract_WCF()
    sys.exit(0)

## if $msg contains 'Recv the  eag module  notify  data user' ##
elif sys.argv[1] == "auth_step2":
    print("call function authentication step2")
    os.system(
        'logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
    ipadd, device_mac, ap_mac, auth_type, user_name, ssid, deassociation = extract_ip_port()
    authentication_step2(ipadd, user_name, ssid)
    sys.exit(0)

## if $msg contains 'Add black list mac' ##
elif sys.argv[1] == "wips":
    print("call function wips")
    os.system(
        'logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
    device_mac, reason = extract_WIPS()
    sys.exit(0)

elif sys.argv[1] == "deauth":
    print("call function deassociation")
    os.system(
        'logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
    ipadd, message_reason = extract_ipadd()
    reason, device_mac, reason_number = extract_reason()
    deassociation(ipadd, device_mac, reason, reason_number)
    try:
        write_api.write(bucket, org, [{"measurement": "support_wlan_deassociation", "tags": {"AP_IPAddr": ipadd, "Client_MAC": device_mac, "Reason_Deassociation": reason, "topic": "deauth"}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 
    os.system('logger -t montag -p user.info Sending email')
    os.system('logger -t montag -p user.info Process terminated')
    sys.exit(0)

elif sys.argv[1] == "roaming":
    print("WLAN Roaming - deauth reason 1")
    os.system(
        'logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
    ipadd, message_reason = extract_ipadd()
    reason, device_mac, reason_number = extract_reason()
    try:
        write_api.write(bucket, org, [{"measurement": "support_wlan_deassociation", "tags": {"AP_IPAddr": ipadd, "Client_MAC": device_mac, "Reason_Deassociation": reason, "topic": "roaming"}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 
    sys.exit(0)

elif sys.argv[1] == "leaving":
    print("WLAN Client disconnection")
    os.system(
        'logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
    ipadd, message_reason = extract_ipadd()
    reason, device_mac, reason_number = extract_reason()
    try:
        write_api.write(bucket, org, [{"measurement": "support_wlan_deassociation", "tags": {"AP_IPAddr": ipadd, "Client_MAC": device_mac, "Reason_Deassociation": reason, "topic": "leaving"}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 
    sys.exit(0)

elif sys.argv[1] == "reboot":
    print("call function reboot")
    os.system(
        'logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
    ipadd, message_reason = extract_ipadd()
    reboot(ipadd)
    os.system('logger -t montag -p user.info Sending email')
    os.system('logger -t montag -p user.info Process terminated')
    sys.exit(0)

elif sys.argv[1] == "unexpected_reboot":
    print("call function reboot")
    os.system(
        'logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
    ipadd, message_reason = extract_ipadd()
    unexpected_reboot(ipadd)
    os.system('logger -t montag -p user.info Sending email')
    os.system('logger -t montag -p user.info Process terminated')
    sys.exit(0)

elif sys.argv[1] == "upgrade":
    print("call function upgrade")
    os.system(
        'logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
    ipadd, message_reason = extract_ipadd()
    upgrade(ipadd)
    os.system('logger -t montag -p user.info Sending email')
    os.system('logger -t montag -p user.info Process terminated')
    sys.exit(0)

elif sys.argv[1] == "exception":
    print("call function exception")
    os.system(
        'logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
    ipadd, message_reason = extract_ipadd()
    exception(ipadd)
    os.system('logger -t montag -p user.info Sending email')
    os.system('logger -t montag -p user.info Process terminated')
    sys.exit(0)

elif sys.argv[1] == "target_asserted":
    print("call function target_asserted")
    os.system(
        'logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
    ipadd, message_reason = extract_ipadd()
    target_asserted(ipadd)
    os.system('logger -t montag -p user.info Sending email')
    os.system('logger -t montag -p user.info Process terminated')
    sys.exit(0)

elif sys.argv[1] == "internal_error":
    print("call function internal_error")
    os.system(
        'logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
    ipadd, message_reason = extract_ipadd()
    internal_error(ipadd)
    os.system('logger -t montag -p user.info Sending email')
    os.system('logger -t montag -p user.info Process terminated')
    sys.exit(0)

elif sys.argv[1] == "kernel_panic":
    print("call function kernel_panic")
    os.system(
        'logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
    ipadd, message_reason = extract_ipadd()
    kernel_panic(ipadd)
    os.system('logger -t montag -p user.info Sending email')
    os.system('logger -t montag -p user.info Process terminated')
    sys.exit(0)

elif sys.argv[1] == "limit_reached":
    print("call function Associated STA limit reached")
    os.system(
        'logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
    ipadd, message_reason = extract_ipadd()
    limit_reached(ipadd)
    os.system('logger -t montag -p user.info Sending email')
    os.system('logger -t montag -p user.info Process terminated')
    sys.exit(0)

else:
    os.system('logger -t montag -p user.info Wrong parameter received')
    print("Wrong parameter received")
    sys.exit(2)
