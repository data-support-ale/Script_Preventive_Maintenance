#!/usr/bin/env python

import sys
import os
import getopt
import json
import logging
import datetime
from time import gmtime, strftime, localtime,sleep
from support_tools import get_credentials,get_server_log_ip,get_jid,get_mail,send_python_file_sftp,get_file_sftp
from support_send_notification import send_message,send_file,send_mail
import subprocess
import re
import pysftp
import requests
import paramiko

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
date = datetime.date.today()
date_hm = datetime.datetime.today()

switch_user, switch_password, jid, gmail_user, gmail_password, mails,ip_server_log = get_credentials()
filename = 'tech_support_complete.tar'

last = ""
with open("/var/log/devices/get_log_switch.json", "r") as log_file:
   for line in log_file:
      last = line

with open("/var/log/devices/get_log_switch.json", "w") as log_file:
   log_file.write(last)

with open("/var/log/devices/get_log_switch.json", "r") as log_file:
   log_json = json.load(log_file)
   ipadd = log_json["relayip"]
   host = log_json["hostname"]
   msg = log_json["message"]
   print(msg)

print("Switch IP Address is: " + ipadd)
print("Switch Hostname is: " + host)
print("Syslog raw message: " + msg)

pattern = ""
if len(sys.argv) > 1:
   pattern = sys.argv[1]
   print(pattern)
   info = ("We received following pattern from RSyslog {0}").format(pattern)
   os.system('logger -t montag -p user.info ' + info)

def get_port():
   with open("/var/log/devices/get_log_switch.json", "r") as log_file:
      log_json = json.load(log_file)
      ipadd = log_json["relayip"]
      host = log_json["hostname"]
      msg = log_json["message"]
      print(msg)
      port = re.findall(r"LINKSTS (.*?) DOWN", msg)[0]
      port = port.replace("\"", "",3)
      port = port.replace("\\", "",3)
      print(port)
      return port

try:
   p = paramiko.SSHClient()
   p.set_missing_host_key_policy(paramiko.AutoAddPolicy())
   p.connect(ipadd, port=22, username="admin", password="switch")
except paramiko.ssh_exception.AuthenticationException:
   print("Authentication failed enter valid user name and password")
   info = ("SSH Authentication failed when connecting to OmniSwitch {0}, we cannot collect logs").format(ipadd)
   os.system('logger -t montag -p user.info {0}').format(info)
   send_message(info,jid)
   sys.exit(0)
except paramiko.ssh_exception.NoValidConnectionsError:
   print("Device unreachable")
   logging.info(runtime + ' SSH session does not establish on OmniSwitch ' + ipadd)
   info = ("OmniSwitch {0} is unreachable, we cannot collect logs").format(ipadd)
   os.system('logger -t montag -p user.info {0}').format(info)
   send_message(info,jid)
   sys.exit(0)
cmd = ("rm -rf {0}").format(filename)
stdin, stdout, stderr = p.exec_command(cmd)
exception = stderr.readlines()
exception = str(exception)
connection_status = stdout.channel.recv_exit_status()
if connection_status != 0:
   info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd,exception)
   send_message(info,jid)
   os.system('logger -t montag -p user.info ' + info)
   sys.exit(2)

stdin, stdout, stderr = p.exec_command("show tech-support eng complete")
exception = stderr.readlines()
exception = str(exception)
connection_status = stdout.channel.recv_exit_status()
if connection_status != 0:
   info = ("\"The show tech support eng complete\" command on OmniSwitch {0} failed - {1}").format(ipadd,exception)
   send_message(info,jid)
   os.system('logger -t montag -p user.info ' + info)
   sys.exit(2)

cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2}  ls | grep {3}".format(switch_password,switch_user,ipadd,filename)
run=cmd.split()
out=''
i=0
while not out:
   print(" Tech Support file creation under progress.", end="\r")
   sleep(2)
   print(" Tech Support file creation under progress..", end="\r")
   sleep(2)
   print(" Tech Support file creation under progress...", end="\r")
   print(i)
   sleep(2)
   p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
   out, err = p.communicate()
   out=out.decode('UTF-8').strip()
   if i > 20:
      print("Tech Support file creation timeout")
      exit()

f_filename= "/tftpboot/{0}_{1}-{2}_{3}_{4}".format(date,date_hm.hour,date_hm.minute,ipadd,filename)
get_file_sftp(switch_user,switch_password,ipadd,filename)

####
port = get_port()
print("port number is : " + port)

##########################Get More LOGS########################################
text = "More logs about the switch : {0} \n\n\n".format(ipadd)

l_switch_cmd = []
l_switch_cmd.append("show virtual-chassis topology")
l_switch_cmd.append("show chassis")

l_switch_cmd.append("echo \"top\" | su")
l_switch_cmd.append("echo \"free -m\" | su")
l_switch_cmd.append("echo \"cat \/proc\/meminfo\" | su")

for switch_cmd in l_switch_cmd:
   cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password,switch_user,ipadd,switch_cmd)
   output=subprocess.check_output(cmd,stderr=subprocess.DEVNULL, shell=True)
   output=output.decode('UTF-8').strip()
   text = "{0}{1}: \n{2}\n\n".format(text,switch_cmd,output)

date = datetime.date.today()
date_hm = datetime.datetime.today()

filename= "{0}_{1}-{2}_{3}_logs".format(date,date_hm.hour,date_hm.minute,ipadd)
f_logs = open('/opt/ALE_Script/{0}.txt'.format(filename),'w')
f_logs.write(text)
f_logs.close()
###############################################################################

if jid !='':
         info = "A Pattern {1} has been detected in switch(IP : {0}) syslogs. A snapshot has been sent in the directory /tftpboot/ on syslog server".format(ipadd,pattern)
         send_message(info,jid)
         send_message(msg,jid)

open('/var/log/devices/get_log_switch.json','w').close()
