#!/usr/local/bin/python3.7

from operator import contains
import sys
import os
import re
import json
import paramiko
import threading
from support_tools_OmniSwitch import isEssential, ssh_connectivity_check, file_setup_qos, format_mac, get_credentials, add_new_save, check_save, script_has_run_recently, send_file
from time import strftime, localtime
from support_send_notification import send_message, send_message_request_advanced, send_message_request
from database_conf import *
import syslog

syslog.openlog('support_switch_duplicate_ip')
syslog.syslog(syslog.LOG_INFO, "Executing script")


runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

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
            filename = "/opt/ALE_Script/configqos"
            th = threading.Thread(
                target=sftp.put, args=(filename, remote_path))
            th.start()
            th.join(120)
        except IOError:
            exception = "File error or wrong path"
            syslog.syslog(syslog.LOG_INFO, "SSH Session - Exception: " + exception)
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
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
            syslog.syslog(syslog.LOG_INFO, "SSH Session - Exception: " + exception)
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
    except paramiko.AuthenticationException:
        exception = "AuthenticationException"
        syslog.syslog(syslog.LOG_INFO, "SSH Session - Exception: " + exception)
        info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
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

    syslog.syslog(syslog.LOG_INFO, "SSH Session for applying configqos file on working directory")
    cmd = "configuration apply ./working/configqos "
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
    syslog.syslog(syslog.LOG_INFO, "configqos file applied on working directory")

# Sample log
# {"@timestamp":"2022-01-05T12:14:46+01:00","type":"syslog_json","relayip":"10.130.7.247","hostname":"os6860","message":"<13>Jan  5 12:14:46 OS6860 ConsLog [slot 1\/1] Wed Jan  5 12:14:46  ipni arp WARN duplicate IP address 10.130.7.247 from port 1\/1\/9 eth addr 38f3ab:592a7e","end_msg":""}
last = ""
with open("/var/log/devices/lastlog_dupip.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_dupip.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_dupip.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
        print(msg)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog IP Address: " + ipadd)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog Hostname: " + host)
        #syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + msg)
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_dupip.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_dupip.jso - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_dupip.jso - Index error in regex")
        exit()
    if "duplicate" in msg:
        try:
            ip_dup, port, mac = re.findall(r"duplicate IP address (.*?) from port (.*?) eth addr (.*)", msg)[0]
        except IndexError:
            try:
                ip_dup, port, mac = re.findall(r"duplicate IP address (.*?) from port (.*?) eth-addr (.*)", msg)[0]
            except IndexError:
                print("Index error in regex")
                syslog.syslog(syslog.LOG_INFO, "Index error in regex")

                exit()
            print("Index error in regex")
            syslog.syslog(syslog.LOG_INFO, "Index error in regex")
            exit()
    # CORE swlogd ipni arp INFO: arp info overwritten for 172.16.29.30 by 78e3b5:054b08 port Lag 1
    elif "overwritten" in msg:
        try:
            ip_dup, mac, port = re.findall(r"arp info overwritten for (.*?) by (.*?) port (.*)", msg)[0]
        except IndexError:
            print("Index error in regex")
            syslog.syslog(syslog.LOG_INFO, "Index error in regex")
            exit()
    else:
        print("No pattern match")
        syslog.syslog(syslog.LOG_INFO, "No pattern match")
        exit()
    syslog.syslog(syslog.LOG_INFO, "Executing function format_mac")        
    mac = format_mac(mac)

function = "duplicate_ip"
if script_has_run_recently(300,ipadd,function):
    print('you need to wait before you can run this again')
    syslog.syslog(syslog.LOG_INFO, "Executing script exit because executed within 5 minutes time period")   
    exit()

# always 1
#never -1
# ? 0
syslog.syslog(syslog.LOG_INFO, "Executing function check_save") 
save_resp = check_save(ipadd, port, "duplicate")
syslog.syslog(syslog.LOG_INFO, "Decisions saved: " + save_resp)
if save_resp == "0":
    if not ("Lag")in port:
        syslog.syslog(syslog.LOG_INFO, "Port is not member of a LinkAgg")  
        feature = "Disable port " + port
        syslog.syslog(syslog.LOG_INFO, "Advanced Feature: " + feature) 
        notif = "Preventive Maintenance Application - An IP address duplication (Duplicate IP: {0}) on port {1} of OmniSwitch {2} / {3} has been detected.\nDo you want to blocklist the MAC Address: {4} ?".format(ip_dup,port,host,ipadd,mac)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Rainbow Adaptive Card of type Advanced")
        answer = send_message_request_advanced(notif, jid,feature)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        syslog.syslog(syslog.LOG_INFO, "Rainbow Adaptive Card Answer: " + answer)
        print(answer)

    else:
        syslog.syslog(syslog.LOG_INFO, "Port is member of a LinkAgg") 
        notif = "Preventive Maintenance Application - An IP address duplication (Duplicate IP: {0}) on port {1} of OmniSwitch {2} / {3} has been detected.\nDo you want to blocklist the MAC Address: {4} ?".format(ip_dup,port,host,ipadd,mac)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Rainbow Adaptive Card")
        answer = send_message_request(notif, jid)  
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

    if isEssential(ip_dup):
        answer = "0"
        notif = "Preventive Maintenance Application - An IP duplication has been detected on your network that involves essential IP Address {} therefore we do not proceed further".format(ip_dup)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Send Notification")
        send_message(notif,jid)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent - exit")
        sys.exit()

    if "e8:e7:32" in format_mac(mac):
        answer = "0"
        notif = "Preventive Maintenance Application - An IP duplication has been detected on your network that involves an OmniSwitch chassis/interfaces MAC-Address therefore we do not proceed further".format(ip_dup)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Send Notification")
        send_message(notif,jid)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent - exit")    
        sys.exit()
       
    if answer == "2":
        syslog.syslog(syslog.LOG_INFO, "Executing function add_new_save")
        add_new_save(ipadd, port, "duplicate", choice="always")
        syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Port: " + port + " Choice: " + " Always")

        answer = '1'
    elif answer == "0":
        syslog.syslog(syslog.LOG_INFO, "Executing function add_new_save")
        add_new_save(ipadd, port, "duplicate", choice="never")
        syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Port: " + port + " Choice: " + " Never")
elif save_resp == "-1":
    print("Decision saved to No - script exit")
    syslog.syslog(syslog.LOG_INFO, "Decision saved to No - script exit")
    try:
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "IP_dup": ip_dup, "mac": mac}, "fields": {"count": 1}}])
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
    enable_qos_ddos(switch_user, switch_password, ipadd, mac)
    if jid != '':
        syslog.syslog(syslog.LOG_INFO, "Executing function enable_qos_ddos")
        notif = "Preventive Maintenance Application - An IP Address duplication has been detected on your network and QOS policy has been applied to prevent access for the MAC Address {0} to device {1}".format(mac, ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Send Notification")
        send_message(notif,jid)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")    
        try:
            write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                "IP": ipadd, "IP_dup": ip_dup, "mac": mac}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass
## Value 3 when we return advanced value like Disable port x/x/x
elif answer == '3':
    syslog.syslog(syslog.LOG_INFO, "Anwser received is " + feature)
    # DISABLE Port
    syslog.syslog(syslog.LOG_INFO, "SSH Session for disabling port")
    cmd = "interfaces port " + port + " admin-state disable"
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
    syslog.syslog(syslog.LOG_INFO, "SSH Session closed")
    filename_path = "/var/log/devices/" + host + "/syslog.log"
    category = "ddos"
    subject = "Preventive Maintenance Application - An IP Address duplication has been detected:".format(host, ipadd)
    action = "An IP Address duplication has been detected on your network and interface port {0} is disabled to prevent access to OmniSwitch {2} / {3}".format(port,ip_dup, host, ipadd)
    result = "Find enclosed to this notification the log collection"
    syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
    syslog.syslog(syslog.LOG_INFO, "Action: " + action)
    syslog.syslog(syslog.LOG_INFO, "Result: " + result)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
    send_file(filename_path, subject, action, result, category, jid)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
    try:
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
            "IP": ipadd, "IP_dup": ip_dup, "mac": mac}, "fields": {"count": 1}}])
        syslog.syslog(syslog.LOG_INFO, "Statistics saved")
    except UnboundLocalError as error:
        print(error)
    except Exception as error:
        print(error)
        pass