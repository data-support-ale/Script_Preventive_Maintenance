#!/usr/bin/env python3

import sys
import os
import re
import json
import paramiko
import threading
from support_tools_OmniSwitch import isEssential, ssh_connectivity_check, file_setup_qos, format_mac, get_credentials
from time import strftime, localtime
from support_send_notification import *
# from database_conf import *
import time
import syslog

syslog.openlog('support_switch_duplicate_ip')
syslog.syslog(syslog.LOG_INFO, "Executing script")

from pattern import set_rule_pattern, set_portnumber, set_decision, get_decision, mysql_save

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

# Script init
script_name = sys.argv[0]

pattern = sys.argv[1]
print(pattern)
set_rule_pattern(pattern)

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

path = os.path.dirname(__file__)

# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company, room_id = get_credentials()


def enable_qos_ddos(user, password, ipadd, ipadd_ddos):
    syslog.syslog(syslog.LOG_INFO, "Executing function enable_qos_ddos")
    syslog.syslog(syslog.LOG_INFO, "Building confiqos file - Executing function file_setup_qos")
    file_setup_qos(ipadd_ddos)

    remote_path = '/flash/working/configqos'
    syslog.syslog(syslog.LOG_INFO, "SSH Session start")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        syslog.syslog(syslog.LOG_INFO, "SSH Session to: " + ipadd)
        ssh.connect(ipadd, username=user, password=password, timeout=20.0)
        syslog.syslog(syslog.LOG_INFO, "SSH Session established")
        sftp = ssh.open_sftp()
        # In case of SFTP Get timeout thread is closed and going into Exception
        try:
            filename = path + "/configqos"
            syslog.syslog(syslog.LOG_INFO, "File " + filename + " pushed by SFTP on OmniSwitch " + ipadd + " path " + remote_path)
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
            send_message(notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,result='failure', reason=notif, exception=exception)
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            except UnboundLocalError as exception:
                print(str(exception)) 
            except Exception as exception:
                print(str(exception))
            syslog.syslog(syslog.LOG_INFO, "Script exit")
            os._exit(1)
        except Exception:
            exception = "SFTP Get Timeout"
            syslog.syslog(syslog.LOG_INFO, "SSH Session - Exception: " + exception)
            notif = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
            send_message(notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,result='failure', reason=notif, exception=exception)
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            except UnboundLocalError as exception:
                print(str(exception)) 
            except Exception as exception:
                print(str(exception))
            syslog.syslog(syslog.LOG_INFO, "Script exit")
            os._exit(1)
    except paramiko.AuthenticationException:
        exception = "AuthenticationException"
        syslog.syslog(syslog.LOG_INFO, "SSH Session - Exception: " + exception)
        notif = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message(notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,result='failure', reason=notif, exception=exception)
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as exception:
            print(str(exception)) 
        except Exception as exception:
            print(str(exception))
        syslog.syslog(syslog.LOG_INFO, "Script exit")
        os._exit(1)

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
                # OS6860E_VC_Core swlogd ipni arp WARN: duplicate IP address 10.130.7.1 from port Lag 10 eth-addr e8e732:079879
                ip_dup, port, mac = re.findall(r"duplicate IP address (.*?) from port (.*?) eth-addr (.*)", msg)[0]
            except IndexError:
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

set_portnumber(port)
if alelog.rsyslog_script_timeout(ipadd + port + pattern, time.time()):
    print("Less than 5 min")
    syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
    exit(0)

syslog.syslog(syslog.LOG_INFO, "Executing function get_decision")
decision = get_decision(ipadd)


if (len(decision) == 0) or (len(decision) == 1 and decision[0] == 'Yes'):
    #notif = "IP address duplication (" + ip_dup + ") on port " + port + " of switch " + ipadd + "(" + host + "). Do you want to blacklist mac : " + mac + " ?"
    # answer = send_message_request(notif, jid)
    if not ("Lag")in port: 
        syslog.syslog(syslog.LOG_INFO, "Port is not member of a LinkAgg")  
        feature = "Disable port " + port
        syslog.syslog(syslog.LOG_INFO, "Advanced Feature: " + feature) 
        notif = "Preventive Maintenance Application - An IP address duplication (Duplicate IP: {0}) on port {1} of OmniSwitch {2} / {3} has been detected.\nDo you want to blocklist the MAC Address: {4} ?".format(ip_dup,port,host,ipadd,mac)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Rainbow Adaptive Card of type Advanced")
        answer = send_message_request_advanced(notif, feature)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        syslog.syslog(syslog.LOG_INFO, "Rainbow Adaptive Card Answer: " + answer)

        set_decision(ipadd, answer)
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif + " Decision received: " + answer, exception='')
        print(answer)
    else:
        syslog.syslog(syslog.LOG_INFO, "Port is member of a LinkAgg") 
        notif = "Preventive Maintenance Application - An IP address duplication (Duplicate IP: {0}) on port {1} of OmniSwitch {2} / {3} has been detected.\nDo you want to blocklist the MAC Address: {4} ?".format(ip_dup,port,host,ipadd,mac)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Rainbow Adaptive Card")
        answer = send_message_request(notif)  
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

        set_decision(ipadd, answer)
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif + " Decision received: " + answer, exception='')
        print(answer)

    if isEssential(ip_dup):
        answer = "0"
        notif = "Preventive Maintenance Application - An IP duplication has been detected on your network that involves essential IP Address {} therefore we do not proceed further".format(ip_dup)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Notification sent")
        answer = send_message(notif) 
        set_decision(ipadd, "4")
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
        syslog.syslog(syslog.LOG_INFO, "Script exit")
        sys.exit()

    if "e8:e7:32" in format_mac(mac):
        answer = "0"
        notif = "Preventive Maintenance Application - An IP duplication has been detected on your network that involves an OmniSwitch chassis/interfaces MAC-Address therefore we do not proceed further".format(ip_dup)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Notification sent")
        answer = send_message(notif) 
        set_decision(ipadd, "4")
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
        syslog.syslog(syslog.LOG_INFO, "Script exit")
        sys.exit()

    if answer == "2":
        answer = '1'

elif 'yes and remember' in [d.lower() for d in decision]:
    answer = '2'
    syslog.syslog(syslog.LOG_INFO, "Decision saved to Yes and remember")

elif 'No' in decision:
    syslog.syslog(syslog.LOG_INFO, "Decision saved to No - script exit")
    sys.exit()
else:
    answer = '1'
    syslog.syslog(syslog.LOG_INFO, "No answer - Decision set to Yes - Script exit - will be called by next occurence") 

syslog.syslog(syslog.LOG_INFO, "Rainbow Acaptive Card answer: " + answer)

if answer == '1':
    syslog.syslog(syslog.LOG_INFO, "Anwser received is Yes")
    syslog.syslog(syslog.LOG_INFO, "Executing function enable_qos_ddos")
    enable_qos_ddos(switch_user, switch_password, ipadd, mac)
    notif = "Preventive Maintenance Application - An IP duplication has been detected on your network and QOS policy has been applied to prevent access for the MAC Address {0} to OmniSwitch {1}/{2}".format(mac, ipadd, host)
    syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
    syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Send Notification")
    send_message(notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")    
    set_decision(ipadd, "4")
    try:
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
        syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision")    
    except UnboundLocalError as error:
        print(error)
        sys.exit()
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
    filename_path = "/var/log/devices/" + host + "/syslog.log"
    category = "ddos"
    subject = "Preventive Maintenance Application - An IP Address duplication has been detected:".format(host, ipadd)
    action = "An IP Address duplication has been detected on your network and interface port {0} is disabled to prevent access to OmniSwitch {2} / {3}".format(port,ip_dup, host, ipadd)
    result = "Find enclosed to this notification the log collection"
    syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
    syslog.syslog(syslog.LOG_INFO, "Action: " + action)
    syslog.syslog(syslog.LOG_INFO, "Result: " + result)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
    send_file(filename_path, subject, action, result, category)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
    set_decision(ipadd, "4")
    try:
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')
        syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision")    
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 
