#!/usr/bin/env python3

import sys
import os
import getopt
import json
import logging
import datetime
from time import gmtime, strftime, localtime,sleep
from support_tools import get_credentials,get_server_log_ip,get_jid,extract_ip_port,get_mail,send_python_file_sftp,get_file_sftp
from support_send_notification import send_message,send_file,send_mail
import subprocess


runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

switch_user, switch_password, jid, gmail_user, gmail_password, mails,ip_server_log = get_credentials()
ip_switch,port = extract_ip_port("get_log_switch")
filename = 'tech_support_complete.tar'


cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2}  rm -rf {3}".format(switch_password,switch_user,ip_switch,filename)
run=cmd.split()
p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)


cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2}  show tech-support eng complete".format(switch_password,switch_user,ip_switch)
run=cmd.split()
p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)



cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2}  ls | grep {3}".format(switch_password,switch_user,ip_switch,filename)
run=cmd.split()
out=''
i=0
while not out:
   i=i+1
   print("wait.", end="\r")
   sleep(2)
   print("wait..", end="\r")
   sleep(2)
   print("wait...", end="\r")
   print(i)
   sleep(2)
   p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
   out, err = p.communicate()
   out=out.decode('UTF-8').strip()
   if i > 20:
      print("timeout")
      exit()


get_file_sftp(switch_user,switch_password,ip_switch,filename)

##########################Get More LOGS########################################
text = "More logs about the switch : {0} \n\n\n".format(ip_switch)

l_switch_cmd = []
l_switch_cmd.append("show unp user")
l_switch_cmd.append("show interfaces macsec")


for switch_cmd in l_switch_cmd:
   cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password,switch_user,ip_switch,switch_cmd)
   run=cmd.split()
   p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
   out, err = p.communicate()
   out=out.decode('UTF-8').strip()

   text = "{0}{1}: \n{2}\n\n".format(text,switch_cmd,out) 



date = datetime.date.today()
date_hm = datetime.datetime.today()

filename= "{0}_{1}-{2}_{3}_logs".format(date,date_hm.hour,date_hm.minute,ip_switch)
f_logs = open('/opt/ALE_Script/{0}.txt'.format(filename),'w')
f_logs.write(text)
f_logs.close()
###############################################################################


if jid !='':
         info = "Log of device : {0}".format(ip_switch)
         send_file(info,jid,ip_switch)
         info = "A Pattern has been detected in switch(IP : {0}) syslogs. A snapshot has been sent in the directory /tftpboot/ on syslog server".format(ip_switch)
         send_message(info,jid)
if gmail_user !='':
         info = "A Pattern has been detected in switch(IP : {0}) syslogs. A snapshot has been sent in the directory /tftpboot/ on syslog server".format(ip_switch)
         subject = "A Pattern has been detected in switch log"
         send_mail(ip_switch,"0",info,subject,gmail_user,gmail_password,mails)



open('/var/log/devices/get_log_switch.json','w').close()
