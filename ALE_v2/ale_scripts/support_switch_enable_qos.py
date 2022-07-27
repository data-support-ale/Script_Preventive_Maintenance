#!/usr/bin/env python3

import sys
import os
import json
import re
import syslog
from support_tools_OmniSwitch import isEssential, get_credentials, ssh_connectivity_check, file_setup_qos
from time import strftime, localtime, sleep
from support_send_notification import *
# from database_conf import *
import paramiko
import threading
import time

from pattern import set_rule_pattern, set_portnumber, set_decision, get_decision, mysql_save

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

path = os.path.dirname(__file__)

_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

def enable_qos_ddos(user, password, ipadd, ipadd_ddos):

    file_setup_qos(ipadd_ddos)
    _runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

    remote_path = '/flash/working/configqos'
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ipadd, username=user, password=password, timeout=20.0)
        sftp = ssh.open_sftp()
        # In case of SFTP Get timeout thread is closed and going into Exception
        try:
            filename = path + "/configqos"
            th = threading.Thread(
                target=sftp.put, args=(filename, remote_path))
            th.start()
            th.join(120)
        except IOError:
            exception = "File error or wrong path"
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            
            send_message(info)
            try:
                mysql_save(runtime=_runtime, ip_address=ipadd, result='failure', reason=info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
        except Exception:
            exception = "SFTP Get Timeout"
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            
            send_message(info)
            try:
                mysql_save(runtime=_runtime, ip_address=ipadd, result='failure', reason=info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
    except paramiko.ssh_exception.AuthenticationException:
        exception = "SFTP Get Timeout"
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        
        send_message(info)
        try:
            mysql_save(runtime=_runtime, ip_address=ipadd, result='failure', reason=info, exception=exception)
        except UnboundLocalError as error:
            print(error)
        sys.exit()  
    
    info = ("The python script execution on OmniSwitch {0}").format(ipadd)
    mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=info, exception='')   
    cmd = "configuration apply ./working/configqos "
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)


# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)

pattern = sys.argv[1]
print(pattern)
set_rule_pattern(pattern)
# info = ("We received following pattern from RSyslog {0}").format(pattern)
# os.system('logger -t montag -p user.info ' + info)

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company, room_id = get_credentials()
last = ""
with open("/var/log/devices/lastlog_ddos_ip.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_ddos_ip.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_ddos_ip.json", "r", errors='ignore') as log_file:
    try:
        port = 0
        log_json = json.load(log_file)
        ip_switch = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
        print(msg)
        ip_switch_ddos = re.findall(r" ([.0-9]*)$", msg)[0]
        try:
            # Log sample if DDOS Attack of type invalid-ip
            # OS6860E swlogd ipni dos WARN: VRF 0: DoS type invalid ipadd from 158.42.253.193/e8:e7:32:fb:47:4b on port 1/1/22
            # Log sample if DDOS Attack of type loopback-src
            # 6860E swlogd ipv4 dos EVENT: CUSTLOG CMM Denial of Service attack detected: <loopback-src>
            # OS6860E swlogd ipni dos WARN: VRF 0: DoS type loopback-src from 127.10.1.65\/2c:fa:a2:c0:fd:a3 on port 1\/1\/6

            ddos_type, ip_switch_ddos, mac_switch_ddos, port = re.findall(r"DoS type (.*?) from (.*?)/(.*?) on port (.*)", msg)[0]
            print(port)
        except:
            ddos_type = "port-scan"
            pass 
        print(ip_switch_ddos)
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_ddos_ip.json empty")
        exit()
    except IndexError:
        print("Index error in regex")
        exit()
    # always 1
    #never -1
    # ? 0
    set_portnumber("0")
    if alelog.rsyslog_script_timeout(ip_switch + "0" + pattern, time.time()):
        print("Less than 5 min")
        exit(0)

    decision = get_decision(ip_switch)
    #save_resp = check_save(ip_switch, "0", "scan")

    #if save_resp == "0":
    if (len(decision) == 0) or (len(decision) == 1 and decision[0] == 'Yes'):
        if port != 0:
            notif = "Preventive Maintenance Application - A DDOS Attack of type {0} has been detected on your network - Source IP Address {1}  on OmniSwitch {2} / {3} port {4}.\nIf you click on Yes, the following actions will be done: Policy action block.".format(ddos_type, ip_switch_ddos, host, ip_switch, port)
            feature = "Disable port " + port
            answer = send_message_request_advanced(notif, feature)
            set_decision(ip_switch, answer)
            mysql_save(runtime=_runtime, ip_address=ip_switch, result='success', reason=notif, exception='')

        else:
            notif = "Preventive Maintenance Application - A DDOS Attack of type {0} has been detected on your network - Source IP Address {1}  on OmniSwitch {2} / {3}.\nIf you click on Yes, the following actions will be done: Policy action block.".format(ddos_type, ip_switch_ddos, host, ip_switch)
            answer = send_message_request(notif)
            set_decision(ip_switch, answer)
            mysql_save(runtime=_runtime, ip_address=ip_switch, result='success', reason=notif, exception='')

        if isEssential(ip_switch_ddos):
            answer = "0"
            notif = "Preventive Maintenance Application - A DDOS Attack has been detected on your network however it involves essential IP Address {} we do not proceed further.".format(ip_switch_ddos)
            print(notif)
            send_message(notif)
            set_decision(ip_switch, "4")
            mysql_save(runtime=_runtime, ip_address=ip_switch, result='success', reason=notif, exception='')
            sys.exit(0)

        if answer == "2":
            answer = '1'

    elif 'No' in decision:
        sys.exit()
    else:
        answer = '1'

    if answer == '1':
        enable_qos_ddos(switch_user, switch_password,ip_switch, ip_switch_ddos)
        os.system('logger -t montag -p user.info Process terminated')
        filename_path = "/var/log/devices/" + host + "/syslog.log"
        subject = "Preventive Maintenance Application - A {0} attack is detected:".format(ddos_type)
        action = "A {0} attack is detected on your network and QOS policy is applied to prevent access for the IP Address {1} to access OmniSwitch {2} / {3}".format(ddos_type, ip_switch_ddos, host, ip_switch)
        result = "Find enclosed to this notification the log collection. More details in the Technical Knowledge Base https://myportal.al-enterprise.com/alebp/s/tkc-redirect?000063327"
        syslog.syslog(syslog.LOG_INFO, "Notification: " + action)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
        send_file(filename_path, subject, action, result, category)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        set_decision(ip_switch_ddos, "4")
        try:
            mysql_save(runtime=_runtime, ip_address=ip_switch_ddos, result='success', reason=notif, exception='')
            syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision")    
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass   


        cmd = "swlog appid ipv4 subapp all level info"
        # ssh session to start python script remotely
        os.system('logger -t montag -p user.info debug3 for ddos  activation')
        os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user, ip_switch, cmd))
        sleep(1)
       # clear lastlog file
        open('/var/log/devices/lastlog_ddos_ip.json', 'w').close

    ## Value 3 when we return advanced value like Disable port x/x/x
    elif answer == '3':
        print("Answer 3 we disable the port")
        os.system('logger -t montag -p user.info Answer 3')
        # DISABLE Port
        cmd = "interfaces port " + port + " admin-state disable"
        ssh_connectivity_check(switch_user, switch_password, ip_switch, cmd)
        filename_path = "/var/log/devices/" + host + "/syslog.log"
        subject = "Preventive Maintenance Application - A DDOS Attack of type invalid-ipadd is detected:".format(host, ip_switch)
        action = "DDOS Attack is detected on your network and interface port {0} is disabled to prevent access to OmniSwitch {2} / {3}".format(port,ip_switch_ddos, host, ip_switch)
        result = "Find enclosed to this notification the log collection."
        send_file(filename_path, subject, action, result, category)
        mysql_save(runtime=_runtime, ip_address=ip_switch, result='success', reason=action, exception='')
        # We disable debugging logs
        cmd = "swlog appid ipv4 subapp all level info"
        ssh_connectivity_check(switch_user, switch_password, ip_switch, cmd)

    else:
        print("Mail request set as no")
        os.system('logger -t montag -p user.info Mail request set as no')
        sleep(1)
        open('/var/log/devices/lastlog_ddos_ip.json', 'w').close()
