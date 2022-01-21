#!/usr/bin/env python

import sys
import os
import json
import logging
import datetime
from time import gmtime, strftime, localtime,sleep
from support_tools_OmniSwitch import get_credentials,get_file_sftp,get_tech_support_sftp,ssh_connectivity_check
from support_send_notification import send_message,send_file,send_mail,send_message_aijaz
import subprocess
import re
from database_conf import *
import threading

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
date = datetime.date.today()
date_hm = datetime.datetime.today()

switch_user,switch_password,jid,gmail_usr,gmail_passwd,mails,ip_server_log,company,mails_raw = get_credentials()
filename = 'tech_support_complete.tar'

last = ""
with open("/var/log/devices/get_log_switch.json", "r", errors='ignore') as log_file:
   for line in log_file:
      last = line

with open("/var/log/devices/get_log_switch.json", "w", errors='ignore') as log_file:
   log_file.write(last)

with open("/var/log/devices/get_log_switch.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/get_log_switch.json empty")
        exit()

pattern = ""
if len(sys.argv) > 1:
   pattern = sys.argv[1]
   print(pattern)
   info = ("We received following pattern from RSyslog {0}").format(pattern)
   os.system('logger -t montag -p user.info ' + info)

def get_port():
   with open("/var/log/devices/get_log_switch.json", "r", errors='ignore') as log_file:
      try:
         log_json = json.load(log_file)
         ipadd = log_json["relayip"]
         host = log_json["hostname"]
         msg = log_json["message"]
      except json.decoder.JSONDecodeError:
         print("File /var/log/devices/get_log_switch.json empty")
         exit()
      port = re.findall(r"LINKSTS (.*?) DOWN", msg)[0]
      port = port.replace("\"", "",3)
      port = port.replace("\\", "",3)
      print(port)
      return port

#if sys.argv[1] == "aijaz":
#   port = get_port()
   #{"@timestamp":"2021-11-22T21:57:06+01:00","type":"syslog_json","relayip":"10.130.7.243","hostname":"sw5-bcb","message":"<134>Nov 22 21:57:06 SW5-BCB swlogd portMgrNi main INFO: : [pmnHALLinkStatusCallback:206] LINKSTS 1\/1\/1 DOWN (gport 0x0) Speed 0 Duplex HALF","end_msg":""}
#   port=str(port)
#   subject = "Preventive Maintenance - Port flapping issue detected on port {0}".format(port)
#   print(subject)
#   info = "A port flapping is noticed on Aijaz lab and we are collecting logs on Server 10.130.7.14 /tftpboot/ directory"
#   send_message_aijaz(subject,info,jid)
#   cmd = "python /flash/python/get_logs_port_flapping.py".format(port)
#   os.system('logger -t montag -p user.info ' + info)
   #os.system("sshpass -p 'switch' ssh -v {0}@{1} {2}".format("admin", ipadd, cmd))
#   try:
#      p = paramiko.SSHClient()
#      p.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#      p.connect(ipadd, port=22, username="admin", password="switch")
#      logging.info(runtime + ' Connecting to OmniSwitch ' + ipadd)
#   except paramiko.ssh_exception.AuthenticationException:
 #     print("Authentication failed enter valid user name and password")
 #     logging.info(runtime + ' SSH Authentication failed when connecting to OmniSwitch ' + ipadd)
#      info = ("SSH Authentication failed when connecting to OmniSwitch {0}, we cannot collect logs").format(ipadd)
 #     os.system('logger -t montag -p user.info ' + info)
 #     send_message_aijaz(subject,info,jid)
#      sys.exit(0)
#   except paramiko.ssh_exception.NoValidConnectionsError:
 #     print("Device unreachable")
 #     logging.info(runtime + ' SSH session does not establish on OmniSwitch ' + ipadd)
 #     info = ("OmniSwitch {0} is unreachable, we cannot collect logs").format(ipadd)
 #     os.system('logger -t montag -p user.info ' + info)
#      send_message_aijaz(subject,info,jid)
 #     sys.exit(0)

 #  stdin, stdout, stderr = p.exec_command(cmd)
 #  exception = stderr.readlines()
 #  exception = str(exception)
 #  connection_status = stdout.channel.recv_exit_status()
  # if connection_status != 0:
 #     info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd,exception)
 #     send_message(info,jid)
 #     os.system('logger -t montag -p user.info ' + info)
 #     sys.exit(2)
 #  sleep(2)
  # filename_aijaz='RZW-Core_logs.txt'
  # with pysftp.Connection(host="10.130.7.243", username="admin", password="switch") as sftp:
 #     remoteFilePath = '/flash/python/RZW-Core_logs.txt'
 #     localFilePath = "/tftpboot/{0}_{1}-{2}_{3}_{4}".format(date,date_hm.hour,date_hm.minute,ipadd,filename_aijaz)
 #     sftp.get(remoteFilePath, localFilePath)
 #  info = "Process finished and logs downloaded"
 #  os.system('logger -t montag -p user.info Process finished and logs downloaded for Aijaz Port flapping issue ')
 #  print(localFilePath)
#   jid1="j_9403700392@openrainbow.com"
 #  url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Test_EMEA"
 #  headers = {  'Content-type':"text/plain",'Content-Disposition': "attachment;filename=port_flapping.log", 'jid1': '{0}'.format(jid),'toto': '{0}'.format(info)}
 #  files = {'file': open(localFilePath,'r')}
 #  response = requests.post(url,files=files, headers=headers)

#if sys.argv[1] == "aijaz2":
   #{"@timestamp":"2021-11-22T21:57:06+01:00","type":"syslog_json","relayip":"10.130.7.248","hostname":"sw5-bcb","message":"2021 Nov 24 15:20:35.139 S_CA_1212_196 swlogd ChassisSupervisor MipMgr EVENT: CUSTLOG CMM Device Power Supply operational state changed to UNPOWERED","end_msg":""}
 #  subject = ("Preventive Maintenance - Power Supply issue detected on switch: {0}").format(ipadd)
 #  print(subject)
 #  info = "A Power Supply is inoperable on your lab"
 #  send_message_aijaz(subject,info,jid)
 #  os.system('logger -t montag -p user.info ' + info)

if jid !='':
         info = "A Pattern {1} has been detected in switch(IP : {0}) syslogs. We are collecting logs on syslog server".format(ipadd,pattern)
         send_message(info,jid)
         send_message(msg,jid)

### TECH-SUPPORT ENG COMPLETE ###
#generate tech_support_sftp(host,ipadd)

f_filename = "tech_support_complete.tar"

#### SFTP GET tech support #####
#get_file_sftp(ipadd,f_filename)

print("Starting collecting additionnal logs")

if jid !='':
         info = "A Pattern {1} has been detected in switch(IP : {0}) syslogs. Tech-support eng complete is collected and stored in /tftpboot/ on syslog server".format(ipadd,pattern)
         send_message(info,jid)
         send_message(msg,jid)

##########################Get More LOGS########################################
text = "More logs about the switch : {0} \n\n\n".format(ipadd)

l_switch_cmd = []
l_switch_cmd.append("show interfaces")
l_switch_cmd.append("show system")
l_switch_cmd.append("show date")
l_switch_cmd.append("show unp user")
print(ipadd)
for switch_cmd in l_switch_cmd:
   cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password,switch_user,ipadd,switch_cmd)
   try:
      output = ssh_connectivity_check(ipadd,switch_cmd)
#      output=subprocess.check_output(target=read_until_EOF, args=(cmd,))
      if output != None:
         #output=output.decode('UTF-8').strip()
         text = "{0}{1}: \n{2}\n\n".format(text,switch_cmd,output)
      else:
         exception = "Timeout"
         info = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
         print(info)
         os.system('logger -t montag -p user.info ' + info)
         send_message(info,jid)
         write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
         sys.exit()         
   except FileNotFoundError as error:
      exception = "FileNotFoundError"
      info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd,exception)
      print(info)
      os.system('logger -t montag -p user.info ' + info)
      send_message(info,jid)
      write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
      sys.exit()

date = datetime.date.today()
date_hm = datetime.datetime.today()

filename= "{0}_{1}-{2}_{3}_logs".format(date,date_hm.hour,date_hm.minute,ipadd)
f_logs = open('/opt/ALE_Script/{0}.txt'.format(filename),'w', errors='ignore')
f_logs.write(text)
f_logs.close()
###############################################################################

filename = '/opt/ALE_Script/{0}.txt'.format(filename)
print(filename)

if jid !='':
         send_file(info,jid,ipadd,filename)

open('/var/log/devices/get_log_switch.json','w').close()
