#!/usr/bin/env python3

import sys
import os
import getopt
import json
import logging
import subprocess
from time import gmtime, strftime, localtime, sleep
import requests
import datetime
#import smtplib
#import mimetypes
import re
from support_tools import get_credentials
from support_send_notification import send_message,send_file,send_alert
import pysftp

#### Example of JSON content
#### {"@timestamp":"2021-11-10T09:42:02.867257+01:00","type":"syslog_json","relayip":"10.130.7.244","hostname":"OS6860N","message":"10:55:46.686 OS6860E-Core2 swlogd COREDUMPER  ALRM: Dumping core for task dpcmm","end_msg":""}
### {"@timestamp":"2021-11-10T09:42:02.867257+01:00","type":"syslog_json","relayip":"10.130.7.244","hostname":"OS6860N","message":"OS6860E-Core2 swlogd PMD main ALRT: PMD generated at /flash/pmd/pmd-agCmm-12.29.2020-11.26.28","end_msg":""}

# Variables
filename = 'tech_support_complete.tar'
filename_pmd = '/flash/pmd/pmd-xx'

script_name = sys.argv[0]
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

uname = os.system('uname -a')
os.system('logger -t montag -p user.info Executing script ' + script_name)

switch_user, switch_password, jid, gmail_user, gmail_password, mails,ip_server_log = get_credentials()

# Function called when Core Dump is observed
def pmd_issue(ipadd,jid):
  os.system('logger -t montag -p user.info PMD Script - A Core DUMP is generated by switch: ' + ipadd[1])
  info = "Switch: {0} - A Core DUMP is generated by switch".format(ipadd)
  send_alert(info,jid)

# Function called for collecting pmd file by SFTP
def get_pmd_sftp(user,password,ipadd,filename_pmd):
   date = datetime.date.today()
   date_hm = datetime.datetime.today()
   pmd_file = filename_pmd.replace("/", "_")
   with pysftp.Connection(host=ipadd, username=user, password=password) as sftp:
      sftp.get('{0}'.format(filename_pmd), '/tftpboot/{0}_{1}_{2}'.format(date,ipadd,pmd_file))         # get a remote file

# Function called for collecting tech_support_complete.tar file by SFTP
def get_tech_support_sftp(user,password,ipadd,filename):
   date = datetime.date.today()
   date_hm = datetime.datetime.today()

   with pysftp.Connection(host=ipadd, username=user, password=password) as sftp:
      sftp.get('./{0}'.format(filename), '/tftpboot/{0}_{1}-{2}_{3}_{4}'.format(date,date_hm.hour,date_hm.minute,ipadd,filename))

# Function called for collecting tech_support_complete.tar and pmd files
def collect_log(ipadd,jid):
  date = datetime.date.today()
  pmd_file = filename_pmd.replace("/", "_")
  pmd_file_rainbow = '/tftpboot/{0}_{1}_{2}'.format(date,ipadd,pmd_file)

  cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2}  rm -rf {3}".format(switch_password,switch_user,ipadd,filename)
  run=cmd.split()
  p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)

  os.system('logger -t montag -p user.info show tech-support eng complete generated ' + str(ipadd))
  cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2}  show tech-support eng complete".format(switch_password,switch_user,ipadd)
  run=cmd.split()
  p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)

  cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2}  ls | grep {3}".format(switch_password,switch_user,ipadd,filename)
  run=cmd.split()
  out=''
  i=0
  while not out:
    i=i+1
    print("Please wait - log ", end="\r")
    sleep(2)
    print("wait..", end="\r")
    sleep(2)
    print("wait...", end="\r")
    print(i)
    sleep(2)
    p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
    out, err = p.communicate()
    out = out.decode('UTF-8').strip()
    print("I" +out+ "I")
    if i > 20:
       print("timeout")
       exit()

  get_pmd_sftp(switch_user,switch_password,ipadd,filename_pmd)
  os.system('logger -t montag -p user.info Core Dump reproduced - logs sent ' + ipadd)
  sleep(2)
  get_tech_support_sftp(switch_user,switch_password,ipadd,filename)
  print(pmd_file_rainbow)
  if jid !='':
         info = "A Core Dump is noticed on switch: {0} syslogs, we are collecting files on server directory {1}".format(ipadd,pmd_file_rainbow)
         send_file(info,jid,ipadd,pmd_file_rainbow)
         send_message(info,jid)

def extract_ipadd():
   last = ""
   with open("/var/log/devices/lastlog_pmd.json", "r") as log_file:
    for line in log_file:
        last = line

   with open("/var/log/devices/lastlog_pmd.json", "w") as log_file:
    log_file.write(last)

   with open("/var/log/devices/lastlog_pmd.json", "r") as log_file:
    log_json = json.load(log_file)
    ipadd = log_json["relayip"]
    host = log_json["hostname"]
    ipadd = str(ipadd)
    print(ipadd)
   return ipadd,host;

def extract_pmd_path():
   last = ""
   with open("/var/log/devices/lastlog_pmd.json", "r") as log_file:
    for line in log_file:
        last = line

   with open("/var/log/devices/lastlog_pmd.json", "w") as log_file:
    log_file.write(last)

   with open("/var/log/devices/lastlog_pmd.json", "r") as log_file:
    log_json = json.load(log_file)
    ipadd = log_json["relayip"]
    host = log_json["hostname"]
    msg =log_json["message"]
    filename_pmd = re.findall(r"PMD generated at (.*)", msg)[0]
    print(filename_pmd)
   return filename_pmd;
  
if sys.argv[1] == "pmd":
      print("Core DUMP - call function pmd_issue")
      os.system('logger -t montag -p user.info Core DUMP - Variable received from rsyslog ' + sys.argv[1])
      ipadd = extract_ipadd()
      pmd_issue(ipadd,jid)
      os.system('logger -t montag -p user.info Core DUMP - Sending Rainbow Notification')
      sys.exit(0)
if sys.argv[1] == "pmd_generated":
      print("Core DUMP - call function collecting log")
      os.system('logger -t montag -p user.info Core DUMP - Variable received from rsyslog ' + sys.argv[1])
      ipadd,host = extract_ipadd()
      filename_pmd = extract_pmd_path()
      collect_log(ipadd,jid)
      os.system('logger -t montag -p user.info Core DUMP - Sending Rainbow Notification')
      sys.exit(0)
else:
      os.system('logger -t montag -p user.info Wrong parameter received ' + sys.argv[1])
      sys.exit(2)

### stop process ###
sys.exit(0)
