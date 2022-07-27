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
os.system('logger -t montag -p user.info Executing script ' + script_name)

pattern = sys.argv[1]
print(pattern)
set_rule_pattern(pattern)
# info = ("We received following pattern from RSyslog {0}").format(pattern)
# os.system('logger -t montag -p user.info ' + info)

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

path = os.path.dirname(__file__)

# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company, room_id = get_credentials()


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
            filename = path + "/configqos"
            th = threading.Thread(
                target=sftp.put, args=(filename, remote_path))
            th.start()
            th.join(120)
        except IOError:
            exception = "File error or wrong path"
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            
            send_message(info)
            try:
                mysql_save(runtime=_runtime, ip_address=ipadd, result='failure', reason=info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
        except Exception:
            exception = "Exception"
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            
            send_message(info)
            try:
                mysql_save(runtime=_runtime, ip_address=ipadd, result='failure', reason=info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
    except paramiko.AuthenticationException:
        exception = "AuthenticationException"
        info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
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
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_dupip.json empty")
        exit()

    if "duplicate" in msg:
        try:
            ip_dup, port, mac = re.findall(r"duplicate IP address (.*?) from port (.*?) eth addr (.*)", msg)[0]
        except IndexError:
            try:
                ip_dup, port, mac = re.findall(r"duplicate IP address (.*?) from port (.*?) eth-addr (.*)", msg)[0]
            except IndexError:
                print("Index error in regex")
                exit()
    # CORE swlogd ipni arp INFO: arp info overwritten for 172.16.29.30 by 78e3b5:054b08 port Lag 1
    elif "overwritten" in msg:
        try:
            ip_dup, mac, port = re.findall(r"arp info overwritten for (.*?) by (.*?) port (.*)", msg)[0]
        except IndexError:
            print("Index error in regex")
            exit()
    else:
        print("No pattern match")
        syslog.syslog(syslog.LOG_INFO, "No pattern match")
        exit()
    mac = format_mac(mac)

# always 1
#never -1
# ? 0
set_portnumber(port)
if alelog.rsyslog_script_timeout(ipadd + port + pattern, time.time()):
    print("Less than 5 min")
    exit(0)

decision = get_decision(ipadd)
# save_resp = check_save(ipadd, port, "duplicate")

# if save_resp == "0":
if (len(decision) == 0) or (len(decision) == 1 and decision[0] == 'Yes'):
    #notif = "IP address duplication (" + ip_dup + ") on port " + port + " of switch " + ipadd + "(" + host + "). Do you want to blacklist mac : " + mac + " ?"
    # answer = send_message_request(notif, jid)
    if not ("Lag")in port: 
        feature = "Disable port " + port
        notif = "Preventive Maintenance Application - An IP address duplication (Duplicate IP: {0}) on port {1} of OmniSwitch {2} / {3} has been detected.\nDo you want to blocklist the MAC Address: {4} ?".format(ip_dup,port,host,ipadd,mac)
        answer = send_message_request_advanced(notif, feature)

        set_decision(ipadd, answer)
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
        print(answer)
    else:
        notif = "Preventive Maintenance Application - An IP address duplication (Duplicate IP: {0}) on port {1} of OmniSwitch {2} / {3} has been detected.\nDo you want to blocklist the MAC Address: {4} ?".format(ip_dup,port,host,ipadd,mac)
        answer =  send_message_request(notif)

        set_decision(ipadd, answer)
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
        print(answer)

    if isEssential(ip_dup):
        answer = "0"
        notif = "Preventive Maintenance Application - An IP duplication has been detected on your network that involves essential IP Address {} therefore we do not proceed further".format(ip_dup)
        send_message_request(notif)
        set_decision(ipadd, "4")
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
        sys.exit()

    if "e8:e7:32" in format_mac(mac):
        answer = "0"
        notif = "Preventive Maintenance Application - An IP duplication has been detected on your network that involves an OmniSwitch chassis/interfaces MAC-Address therefore we do not proceed further".format(ip_dup)
        send_message_request(notif)
        set_decision(ipadd, "4")
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')

        sys.exit()

    if answer == "2":
        answer = '1'

elif 'yes and remember' in [d.lower() for d in decision]:
    answer = '2'

elif 'No' in decision:
    sys.exit()
else:
    answer = '1'

if answer == '1':
    os.system('logger -t montag -p user.info Process terminated')
    enable_qos_ddos(switch_user, switch_password, ipadd, mac)
    notif = "Preventive Maintenance Application - An IP duplication has been detected on your network and QOS policy has been applied to prevent access for the MAC Address {0} to OmniSwitch {1}/{2}".format(mac, ipadd, host)
    syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
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
    os.system('logger -t montag -p user.info Process terminated')
    # DISABLE Port
    cmd = "interfaces port " + port + " admin-state disable"
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
    filename_path = "/var/log/devices/" + host + "/syslog.log"
    category = "ddos"
    subject = "Preventive Maintenance Application - An IP Address duplication has been detected:".format(host, ipadd)
    action = "An IP Address duplication has been detected on your network and interface port {0} is disabled to prevent access to OmniSwitch {2} / {3}".format(port,ip_dup, host, ipadd)
    result = "Find enclosed to this notification the log collection"
    send_file(filename_path, subject, action, result, category)
    mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')
