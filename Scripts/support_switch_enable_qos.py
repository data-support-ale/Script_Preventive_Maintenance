#!/usr/local/bin/python3.7

import sys
import os
import json
import re
from support_tools_OmniSwitch import get_credentials, isEssential, ssh_connectivity_check, file_setup_qos, add_new_save, check_save, script_has_run_recently, send_file
from time import gmtime, strftime, localtime, sleep
from support_send_notification import send_message, send_message_request, send_message_request_advanced
from database_conf import *
import paramiko
import threading


def enable_qos_ddos(user, password, ipadd, ipadd_ddos):

    file_setup_qos(ipadd_ddos)

    remote_path = '/flash/working/configqos'
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ipadd, username=user, password=password, timeout=20.0)
        sftp = ssh.open_sftp()
        # In case of SFTP Get timeout thread is closed and going into Exception
        try:
            filename = "/opt/ALE_Script/configqos"
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
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                    "Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass
        except Exception:
            exception = "SFTP Get Timeout"
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                    "Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass
            sys.exit()
    except paramiko.ssh_exception.AuthenticationException:
        exception = "SFTP Get Timeout"
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                "Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass  
        
    cmd = "configuration apply ./working/configqos "
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
    try:
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "DDOS": ipadd_ddos}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 


# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()
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
            # OS6860E swlogd ipni dos WARN: VRF 0: DoS type invalid ip from 158.42.253.193/e8:e7:32:fb:47:4b on port 1/1/22
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
    save_resp = check_save(ip_switch_ddos, "0", "ddos")

    if save_resp == "0":

        if port != 0:
            notif = "Preventive Maintenance Application - A DDOS Attack of type {0} has been detected on your network - Source IP Address {1}  on OmniSwitch {2} / {3} port {4}.\nIf you click on Yes, the following actions will be done: Policy action block.".format(ddos_type, ip_switch_ddos, host, ip_switch, port)
            feature = "Disable port " + port
            answer = send_message_request_advanced(notif, jid,feature)
        else:
            notif = "Preventive Maintenance Application - A DDOS Attack of type {0} has been detected on your network - Source IP Address {1}  on OmniSwitch {2} / {3}.\nIf you click on Yes, the following actions will be done: Policy action block.".format(ddos_type, ip_switch_ddos, host, ip_switch)
            answer = send_message_request(notif, jid)

        if isEssential(ip_switch_ddos):
                answer = "0"
                info = "Preventive Maintenance Application - A DDOS Attack has been detected on your network however it involves essential IP Address {} we do not proceed further.".format(ip_switch_ddos)
                send_message(info,jid)

        if answer == "2":
            add_new_save(ip_switch_ddos, "0", "ddos", choice="always")
            answer = '1'
        elif answer == "0":
            add_new_save(ip_switch_ddos, "0", "ddos", choice="never")
    elif save_resp == "-1":
        try:
            write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ip_switch, "DDOS": ip_switch_ddos}, "fields": {"count": 1}}])
            sys.exit()   
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            sys.exit() 
    else:
        answer = '1'

    if answer == '1':
        enable_qos_ddos(switch_user, switch_password,
                        ip_switch, ip_switch_ddos)
        os.system('logger -t montag -p user.info Process terminated')
        filename_path = "/var/log/devices/" + host + "/syslog.log"
        category = "ddos"
        subject = "Preventive Maintenance Application - A {0} attack is detected:".format(ddos_type)
        action = "A {0} attack is detected on your network and QOS policy is applied to prevent access for the IP Address {1} to access OmniSwitch {2} / {3}".format(ddos_type, ip_switch_ddos, host, ip_switch)
        result = "Find enclosed to this notification the log collection. More details in the Technical Knowledge Base https://myportal.al-enterprise.com/alebp/s/tkc-redirect?000063327"
        send_file(filename_path, subject, action, result, category, jid)
        
        # We disable debugging logs
        cmd = "swlog appid ipv4 subapp all level info"
        ssh_connectivity_check(switch_user, switch_password, ip_switch, cmd)
        os.system('logger -t montag -p user.info disabling debugging')
        os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
            switch_password, switch_user, ip_switch, cmd))
        sleep(1)
       # clear lastlog file
        open('/var/log/devices/lastlog_ddos_ip.json', 'w').close

    ## Value 3 when we return advanced value like Disable port x/x/x
    elif answer == '3':
        os.system('logger -t montag -p user.info Process terminated')
        # DISABLE Port
        cmd = "interfaces port " + port + " admin-state disable"
        ssh_connectivity_check(switch_user, switch_password, ip_switch, cmd)
        filename_path = "/var/log/devices/" + host + "/syslog.log"
        category = "ddos"
        subject = "Preventive Maintenance Application - A DDOS Attack of type invalid-ip is detected:".format(host, ip_switch)
        action = "DDOS Attack is detected on your network and interface port {0} is disabled to prevent access to OmniSwitch {2} / {3}".format(port,ip_switch_ddos, host, ip_switch)
        result = "Find enclosed to this notification the log collection."
        send_file(filename_path, subject, action, result, category, jid)
        # We disable debugging logs
        cmd = "swlog appid ipv4 subapp all level info"
        ssh_connectivity_check(switch_user, switch_password, ip_switch, cmd)

    else:
        print("Mail request set as no")
        os.system('logger -t montag -p user.info Mail request set as no')
        sleep(1)
        open('/var/log/devices/lastlog_ddos_ip.json', 'w').close()
