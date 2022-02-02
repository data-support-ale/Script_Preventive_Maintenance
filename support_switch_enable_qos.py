#!/usr/bin/env python

import sys
import os
import json
import re
import pysftp
from support_tools_OmniSwitch import get_credentials, ssh_connectivity_check, file_setup_qos, add_new_save, check_save
from time import gmtime, strftime, localtime, sleep
from support_send_notification import send_message,send_file, send_message_request
from database_conf import *
import paramiko
import threading


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
   ssh_connectivity_check(switch_user,switch_password,ipadd,cmd)  

#Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

#Get informations from logs.
switch_user,switch_password,mails,jid,ip_server,login_AP,pass_AP,tech_pass,random_id,company = get_credentials()
last = ""
with open("/var/log/devices/lastlog_ddos.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_ddos.json","w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_ddos.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ip_switch = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_ddos.json empty")
        exit()


last = ""
with open("/var/log/devices/lastlog_ddos.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_ddos.json","w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_ddos.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ip_switch_ddos = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_ddos.json empty")
        exit()

    subject = "A port scan has been detected on your network "

    #always 1 
    #never -1
    #? 0
    save_resp = check_save(ip_switch,"0","scan")

    if save_resp == "0":
        notif = "A port scan has been detected on your network by the IP Address {0}  on device {1}. (if you click on Yes, the following actions will be done: Policy action block)".format(ip_switch_ddos, ip_switch)
        answer = send_message_request(notif,jid)
        if answer == "2":
            add_new_save(ip_switch,"0","scan",choice = "always")
            answer = '1'
        elif answer == "0":
            add_new_save(ip_switch,"0","scan",choice = "never")
    elif save_resp == "-1":
        sys.exit()
    else:
        answer = '1'

    if answer == '1':
          enable_qos_ddos(switch_user,switch_password,ip_switch,ip_switch_ddos)
          os.system('logger -t montag -p user.info Process terminated')
          if jid !='':
            info = "Log of device : {0}".format(ip_switch)
            send_file(info,jid,ip_switch)
            info = "A port scan has been detected on your network and QOS policy has been applied to prevent access for the IP Address {0} to device {1}".format(ip_switch_ddos, ip_switch)
            send_message(info,jid)

          cmd = "swlog appid ipv4 subapp all level info"
          #ssh session to start python script remotely
          os.system('logger -t montag -p user.info debug3 for ddos  activation')
          os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user, ip_switch, cmd))
          sleep(1)
         # clear lastlog file
          open('/var/log/devices/lastlog_ddos_ip.json','w').close 
    else:
       print("Mail request set as no")
       os.system('logger -t montag -p user.info Mail request set as no')
       sleep(1)
       open('/var/log/devices/lastlog_ddos_ip.json','w').close()

