#!/usr/bin/env python

import sys
import os
import re
import json
import paramiko
import threading
from support_tools_OmniSwitch import ssh_connectivity_check, file_setup_qos, format_mac,get_credentials
from time import strftime, localtime
from support_send_notification import send_message, send_mail,send_file
from support_response_handler import request_handler_rainbow
from database_conf import *

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user,switch_password,mails,jid,ip_server,login_AP,pass_AP,tech_pass,random_id,company = get_credentials()

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
        ip = log_json["relayip"]
        nom = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_dupip.json empty")
        exit()


    ip_dup, port, mac = re.findall(r"duplicate IP address (.*?) from port (.*?) eth addr (.*)", msg)[0]
    mac = format_mac(mac)

def enable_qos_ddos(user,password,ipadd,ipadd_ddos):

   file_setup_qos(ipadd_ddos)
   
   remote_path = '/flash/working/configqos'
   ssh = paramiko.SSHClient()
   ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
   try:
        ssh.connect(ipadd, username=user, password=password, timeout=20.0)
        sftp = ssh.open_sftp()
        ## In case of SFTP Get timeout thread is closed and going into Exception
        try:
            filename = "/opt/ALE_Script/configqos"
            th = threading.Thread(target=sftp.put, args=(filename,remote_path))
            th.start()
            th.join(120)
        except IOError:
            exception = "File error or wrong path"
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd,exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info,jid)
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            sys.exit()
        except Exception:
            exception = "SFTP Get Timeout"
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd,exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info,jid)
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            sys.exit()
   except paramiko.ssh_exception.AuthenticationException:
      exception = "SFTP Get Timeout"
      info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd,exception)
      print(info)
      os.system('logger -t montag -p user.info ' + info)
      send_message(info,jid)
      write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
      sys.exit()

   cmd = "configuration apply ./working/configqos "
   ssh_connectivity_check(ipadd,cmd)  

if jid != '':
    notif = "IP address duplication (" + ip_dup + ") on port " + port + " of switch " + ip + "(" + nom + "). Do you want to blacklist mac : " + mac + " ?"
    answer = request_handler_rainbow(ip,'0',port,'0',notif,jid,ip_server,switch_user,"duplicate") #new method
else:
    answer = '1'

if answer == '1':
    os.system('logger -t montag -p user.info Process terminated')
    enable_qos_ddos(switch_user,switch_password,ip,mac)
    if jid != '':
        info = "Log of device : {0}".format(ip)
        send_file(info, jid, ip)
        info = "A IP duplication has been detected on your network and QOS policy has been applied to prevent access for the MAC Address {0} to device {1}".format(mac, ip)
        send_message(info, jid)

from database_conf import *
write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ip, "IP_dup": ip_dup, "mac" : mac}, "fields": {"count": 1}}])
