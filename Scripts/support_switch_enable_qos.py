#!/usr/local/bin/python3.7

import sys
import os
import json
import re
from support_tools_OmniSwitch import get_credentials, isEssential, ssh_connectivity_check, file_setup_qos, add_new_save, check_save, script_has_run_recently
from time import gmtime, strftime, localtime, sleep
from support_send_notification import *
from database_conf import *
import traceback
import paramiko
import threading
import syslog

syslog.openlog('support_switch_enable_qos')
syslog.syslog(syslog.LOG_INFO, "Executing script")
dir="/opt/ALE_Script"
attachment_path = "/var/log/server/log_attachment"
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]

switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

def enable_qos_ddos(user, password, ipadd, ipadd_ddos):
    syslog.syslog(syslog.LOG_INFO, "Executing function enable_qos_ddos")
    file_setup_qos(ipadd_ddos)

    remote_path = '/flash/working/configqos'
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        syslog.syslog(syslog.LOG_INFO, "SSH Session to: " + ipadd)
        ssh.connect(ipadd, username=user, password=password, timeout=20.0)
        sftp = ssh.open_sftp()
        # In case of SFTP Get timeout thread is closed and going into Exception
        try:
            filename = dir + "/configqos"
            th = threading.Thread(
                target=sftp.put, args=(filename, remote_path))
            th.start()
            th.join(120)
        except IOError:
            exception = "File error or wrong path"
            syslog.syslog(syslog.LOG_INFO, "SSH Session - Exception: " + exception)
            notif = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
            send_message_detailed(notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                    "Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass
        except threading.ThreadError as exception:
            syslog.syslog(syslog.LOG_DEBUG, "{0!s}".format(traceback.format_exc(chain=False,limit=None).encode("utf-8")))
            print(exception)
            syslog.syslog(syslog.LOG_INFO, "SFTP Session aborted reason: " + exception)
            pass       
    except TimeoutError as exception:
        syslog.syslog(syslog.LOG_DEBUG, "{0!s}".format(traceback.format_exc(chain=False,limit=None).encode("utf-8")))
        exception = "SSH Timeout"
        syslog.syslog(syslog.LOG_INFO, "Exception: " + str(exception))
        print("Function ssh_connectivity_check - Exception: " + str(exception))
        print("Function ssh_connectivity_check - Timeout when establishing SSH Session")
        notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message_detailed(notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "Timed out", "IP_Address": ipadd}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as exception:
            print(exception)
        except Exception as exception:
            print(exception)
        syslog.syslog(syslog.LOG_INFO, "Script exit")
        os._exit(1)
    except paramiko.AuthenticationException:
        syslog.syslog(syslog.LOG_DEBUG, "{0!s}".format(traceback.format_exc(chain=False,limit=None).encode("utf-8")))
        exception = "AuthenticationException"
        syslog.syslog(syslog.LOG_INFO, "Exception: " + str(exception))
        print("Function ssh_connectivity_check - Authentication failed enter valid user name and password")
        notif = ("SSH Authentication failed when connecting to OmniSwitch {0}, we cannot collect logs or proceed for remediation action").format(ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message_detailed(notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "AuthenticationException", "IP_Address": ipadd}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as exception:
            print(exception)
            return exception 
        except Exception as exception:
            print(exception)
            return exception 
        syslog.syslog(syslog.LOG_INFO, "Script exit")
        os._exit(1)
    except paramiko.SSHException as error:
        syslog.syslog(syslog.LOG_DEBUG, "{0!s}".format(traceback.format_exc(chain=False,limit=None).encode("utf-8")))
        syslog.syslog(syslog.LOG_INFO, "Exception: " + str(exception))
        print("Function ssh_connectivity_check - " + str(exception))
        #exception = exception.readlines()
        exception = str(exception)
        print("Function ssh_connectivity_check - Device unreachable")
        syslog.syslog(syslog.LOG_INFO, " SSH session does not establish on OmniSwitch " + ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        notif = ("OmniSwitch {0} is unreachable, we cannot collect logs").format(ipadd)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message_detailed(notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "DeviceUnreachable", "IP_Address": ipadd}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as exception:
            print(exception)
            return exception
        except Exception as exception:
            print(exception)
            return exception
        ssh.close()
        syslog.syslog(syslog.LOG_INFO, "SSH Session end")
        syslog.syslog(syslog.LOG_INFO, "Script exit")  
        os._exit(1)
    ssh.close()

    syslog.syslog(syslog.LOG_INFO, "SSH Session for applying configqos file on working directory")
    cmd = "configuration apply ./working/configqos "
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
    syslog.syslog(syslog.LOG_INFO, "configqos file applied on working directory")

    try:
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "DDOS": ipadd_ddos}, "fields": {"count": 1}}])
        syslog.syslog(syslog.LOG_INFO, "Statistics saved")

    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 


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
        syslog.syslog(syslog.LOG_DEBUG, "Syslog IP Address: " + ip_switch)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog Hostname: " + host)
        #syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + msg)
        ip_switch_ddos = re.findall(r" ([.0-9]*)$", msg)[0]
        syslog.syslog(syslog.LOG_DEBUG, "Regex DDOS IP: " + ip_switch_ddos)
        try:
            # Log sample if DDOS Attack of type invalid-ip
            # OS6860E swlogd ipni dos WARN: VRF 0: DoS type invalid ip from 158.42.253.193/e8:e7:32:fb:47:4b on port 1/1/22
            # Log sample if DDOS Attack of type loopback-src
            # 6860E swlogd ipv4 dos EVENT: CUSTLOG CMM Denial of Service attack detected: <loopback-src>
            # OS6860E swlogd ipni dos WARN: VRF 0: DoS type loopback-src from 127.10.1.65\/2c:fa:a2:c0:fd:a3 on port 1\/1\/6

            ddos_type, ip_switch_ddos, mac_switch_ddos, port = re.findall(r"DoS type (.*?) from (.*?)/(.*?) on port (.*)", msg)[0]
            print(port)
            syslog.syslog(syslog.LOG_DEBUG, "Regex DDOS IP: " + ip_switch_ddos + "DDOS Type: " + ddos_type + " Port: " + port)
        
        except:
            ddos_type = "port-scan"
            pass 
        print(ip_switch_ddos)
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_ddos_ip.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_ddos_ip.json JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_ddos_ip.json Index error in regex")
        exit()

    # always 1
    #never -1
    # ? 0
    syslog.syslog(syslog.LOG_INFO, "Executing function check_save")
    save_resp = check_save(ip_switch_ddos, "0", "ddos")

    if save_resp == "0":

        if port != 0:
            syslog.syslog(syslog.LOG_INFO, "Port different than 0")
            notif = "Preventive Maintenance Application - A DDOS Attack of type {0} has been detected on your network - Source IP Address {1}  on OmniSwitch {2} / {3} port {4}.\nIf you click on Yes, the following actions will be done: Policy action block.".format(ddos_type, ip_switch_ddos, host, ip_switch, port)
            feature = "Disable port " + port
            syslog.syslog(syslog.LOG_INFO, "Advanced Feature: " + feature) 
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Rainbow Adaptive Card of type Advanced")
            answer = send_message_request_advanced(notif, feature)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            syslog.syslog(syslog.LOG_INFO, "Rainbow Adaptive Card Answer: " + answer)
        else:
            notif = "Preventive Maintenance Application - A DDOS Attack of type {0} has been detected on your network - Source IP Address {1}  on OmniSwitch {2} / {3}.\nIf you click on Yes, the following actions will be done: Policy action block.".format(ddos_type, ip_switch_ddos, host, ip_switch)
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Rainbow Adaptive Card")
            answer = send_message_request_detailed(notif)  
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

        if isEssential(ip_switch_ddos):
                answer = "0"
                notif = "Preventive Maintenance Application - A DDOS Attack has been detected on your network however it involves essential IP Address {} we do not proceed further.".format(ip_switch_ddos)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Send Notification")
                send_message_detailed(notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent - exit")
                sys.exit()

        if answer == "2":
            syslog.syslog(syslog.LOG_INFO, "Executing function add_new_save")
            add_new_save(ip_switch_ddos, "0", "ddos", choice="always")
            syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ip_switch_ddos + " Choice: " + " Always")
            answer = '1'
        elif answer == "0":
            syslog.syslog(syslog.LOG_INFO, "Executing function add_new_save")
            add_new_save(ip_switch_ddos, "0", "ddos", choice="never")
            syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ip_switch_ddos + " Choice: " + " Always")
    elif save_resp == "-1":
        syslog.syslog(syslog.LOG_INFO, "Decision saved to No - script exit")
        try:
            write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ip_switch, "DDOS": ip_switch_ddos}, "fields": {"count": 1}}])
            sys.exit()   
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            sys.exit() 
    
    elif save_resp == "1":
        answer = '2'
        print("Decision saved to Yes and remember")
        syslog.syslog(syslog.LOG_INFO, "Decision saved to Yes and remember")

    else:
        answer = '1'
        syslog.syslog(syslog.LOG_INFO, "No answer - Decision set to Yes - Script exit - will be called by next occurence")    

    syslog.syslog(syslog.LOG_INFO, "Rainbow Acaptive Card answer: " + answer)

    if answer == '1':
        syslog.syslog(syslog.LOG_INFO, "Anwser received is Yes")
        syslog.syslog(syslog.LOG_INFO, "Executing function enable_qos_ddos")
        enable_qos_ddos(switch_user, switch_password,ip_switch, ip_switch_ddos)
        filename_path = "/var/log/devices/" + host + "/syslog.log"
        category = "ddos"
        subject = "Preventive Maintenance Application - A {0} attack is detected:".format(ddos_type)
        action = "A {0} attack is detected on your network and QOS policy is applied to prevent access for the IP Address {1} to access OmniSwitch {2} / {3}".format(ddos_type, ip_switch_ddos, host, ip_switch)
        result = "Find enclosed to this notification the log collection. More details in the Technical Knowledge Base https://myportal.al-enterprise.com/alebp/s/tkc-redirect?000063327"
        syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
        syslog.syslog(syslog.LOG_INFO, "Action: " + action)
        syslog.syslog(syslog.LOG_INFO, "Result: " + result)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")            
        send_file_detailed(filename_path, subject, action, result, category)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        
        # We disable debugging logs
        cmd = "swlog appid ipv4 subapp all level info"
        syslog.syslog(syslog.LOG_INFO, "SSH Session for disabling log verbosity - swlog appid ipv4 subapp all level info")
        ssh_connectivity_check(switch_user, switch_password, ip_switch, cmd)

        #os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user, ip_switch, cmd))
        syslog.syslog(syslog.LOG_INFO, "SSH Session close - debugging disabled")
        sleep(1)
       # clear lastlog file
        open('/var/log/devices/lastlog_ddos_ip.json', 'w').close

    ## Value 3 when we return advanced value like Disable port x/x/x
    elif answer == '3':
        syslog.syslog(syslog.LOG_INFO, "Anwser received is " + feature)
        # DISABLE Port
        syslog.syslog(syslog.LOG_INFO, "SSH Session for disabling port")
        cmd = "interfaces port " + port + " admin-state disable"
        ssh_connectivity_check(switch_user, switch_password, ip_switch, cmd)
        syslog.syslog(syslog.LOG_INFO, "SSH Session closed")
        filename_path = "/var/log/devices/" + host + "/syslog.log"
        category = "ddos"
        subject = "Preventive Maintenance Application - A DDOS Attack of type invalid-ip is detected:".format(host, ip_switch)
        action = "DDOS Attack is detected on your network and interface port {0} is disabled to prevent access to OmniSwitch {2} / {3}".format(port,ip_switch_ddos, host, ip_switch)
        result = "Find enclosed to this notification the log collection."
        syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
        syslog.syslog(syslog.LOG_INFO, "Action: " + action)
        syslog.syslog(syslog.LOG_INFO, "Result: " + result)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")            
        send_file_detailed(filename_path, subject, action, result, category)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        # We disable debugging logs
        syslog.syslog(syslog.LOG_INFO, "SSH Session for disabling log verbosity - swlog appid ipv4 subapp all level info")
        cmd = "swlog appid ipv4 subapp all level info"
        ssh_connectivity_check(switch_user, switch_password, ip_switch, cmd)
        syslog.syslog(syslog.LOG_INFO, "SSH Session close - debugging disabled")

    else:
        print("Script support_enable_qos no pattern match - exiting script")
        syslog.syslog(syslog.LOG_INFO, "Script support_enable_qos no pattern match - exiting script")
        sys.exit()
        open('/var/log/devices/lastlog_ddos_ip.json', 'w').close()
