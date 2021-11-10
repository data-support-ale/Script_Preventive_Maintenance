#!/usr/bin/env python3

import sys
import os
import getopt
import json
import logging
from time import gmtime, strftime, localtime, sleep
import requests
import smtplib
import mimetypes
import re
import datetime
from time import gmtime, strftime, localtime,sleep
from support_tools import get_credentials,get_server_log_ip,get_jid,extract_ip_port,get_mail,send_python_file_sftp,get_file_sftp
from support_send_notification import send_message,send_file,send_mail
import subprocess

script_name = sys.argv[0]
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

uname = os.system('uname -a')
os.system('logger -t montag -p user.info Executing script ' + script_name)

#hostname = sys.argv[2]
#path = os.path.join('/var/log/devices',hostname,'lastlog_macsec_event.json')

def get_jid():
     """
     This function collects Rainbow JID in the file ALE_script.conf.

     :param:                         None
     :return str jip:  Rainbow JID.
     """

     content_variable = open ('/opt/ALE_Script/ALE_script.conf','r')
     file_lines = content_variable.readlines()
     content_variable.close()
     credentials_line = file_lines[0]
     credentials_line_split = credentials_line.split(',')
     jid= credentials_line_split[3]
     return jid

def change(ipadd,port,jid):
  #ssh session to start python script remotely
  os.system('logger -t montag -p user.info MAC-SEC LINK CHANGE noticed on Switch ' + ipadd)
  info = "Switch: {0} MAC-SEC Link CHANGED on port {1}".format(ipadd,port)
  send_message(info,jid)

def retire(ipadd,port,ip,jid):
  #ssh session to start python script remotely
  os.system('logger -t montag -p user.info MAC-SEC LINK RETIRE noticed on Switch ' + ipadd)
  info = "Switch: {0} MAC-SEC Link RETIRED on port {1}".format(ipadd,port)
  send_message(info,jid)
#  collect_log(ip)

def macsec_secured(ipadd,jid):
  #ssh session to start python script remotely
  os.system('logger -t montag -p user.info MAC-SEC LINK SECURED ' + ipadd)
  info = "Switch: {0} MAC-SEC Link SECURED".format(ipadd)
  send_message(info,jid)

def delete_mka(ipadd,jid):
  #ssh session to start python script remotely
  os.system('logger -t montag -p user.info MAC-SEC MKA Removed ' + ipadd)
  info = "Switch: {0} MAC-SEC MKA Removed".format(ipadd)
  send_message(info,jid)

def delete_sa(ipadd,jid):
  #ssh session to start python script remotely
  os.system('logger -t montag -p user.info MAC-SEC Secure Association Removed ' + ipadd)
  info = "Switch: {0} MAC-SEC Secure Association Removed".format(ipadd)
  send_message(info,jid)

def collect_log(ip):
  text = "More logs about the switch : {0} \n\n\n".format(ip)

  l_switch_cmd = []
  l_switch_cmd.append("show interfaces status")
  l_switch_cmd.append("show interfaces macsec")
  l_switch_cmd.append("show interfaces macsec dynamic")

  for switch_cmd in l_switch_cmd:
    cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format("switch","admin",ip,switch_cmd)
    run=cmd.split()
    p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
    out, err = p.communicate()
    out=out.decode('UTF-8').strip()

    text = "{0}{1}: \n{2}\n\n".format(text,switch_cmd,out) 

  date = datetime.date.today()
  date_hm = datetime.datetime.today()

  filename= "{0}_{1}-{2}_{3}_logs".format(date,date_hm.hour,date_hm.minute,ip)
  f_logs = open('/opt/ALE_Script/{0}.txt'.format(filename),'w')
  f_logs.write(text)
  f_logs.close()
  info = "collecting logs"
  filename_path = "/opt/ALE_Script/{0}.txt".format(filename)
  print(filename_path)
#  send_file(info,jid,ip,filename_path)
  info = "Log of device : {0}".format(ip)
  url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotifFile/"
  headers = {  'Content-type':"text/plain",'Content-Disposition': "attachment;filename=journal.txt", 'jid1': '{0}'.format(jid),'toto': '{0}'.format(info)}
  files = {'file': open(filename_path,'rb')}
  response = requests.post(url,files=files, headers=headers)

# Get informations from logs.
def extract_port():
   last = ""
   port = 0
   with open("/var/log/devices/lastlog_macsec.json", "r") as log_file:
    for line in log_file:
        last = line

   with open("/var/log/devices/lastlog_macsec.json", "w") as log_file:
    log_file.write(last)

   with open("/var/log/devices/lastlog_macsec.json", "r") as log_file:
    log_json = json.load(log_file)
    ip = log_json["relayip"]
    ipadd = log_json["hostname"]
    msg = log_json["message"]
    ipadd = str(ipadd)
    port = re.findall(r"gport=(.*)", msg)[0]
    port = int(port) + 1
    print(port)
    print(ipadd)
   return ip,ipadd,port;

#def extract_hostname():
#   last = ""
#  with open("/var/log/devices/lastlog_macsec.json", "r") as log_file:
#    for line in log_file:
#        last = line

#  with open("/var/log/devices/lastlog_macsec.json", "w") as log_file:
#    log_file.write(last)

#  with open("/var/log/devices/lastlog_macsec.json", "r") as log_file:
#    log_json = json.load(log_file)
#    ip = log_json["relayip"]
#    host = log_json["hostname"]
#    msg = log_json["message"]
#  return host;

#host = extract_hostname()   #returning relayIP and port number where loop detected
ip,ipadd,port = extract_port()
jid = get_jid()
print(jid)
script_name = sys.argv[0]

if sys.argv[1] == "macsec":
      print("call function MAC SEC")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      macsec_secured(ipadd,jid)
      os.system('logger -t montag -p user.info Sending Rainbow Notification')
      sys.exit(0)
if sys.argv[1] == "delete_mka":
      print("call function MAC SEC")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      delete_mka(ipadd,jid)
      os.system('logger -t montag -p user.info Sending Rainbow Notification')
      sys.exit(0)
if sys.argv[1] == "delete_sa":
      print("call function MAC SEC")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      delete_sa(ipadd,jid)
      os.system('logger -t montag -p user.info Sending Rainbow Notification')
      sys.exit(0)
if sys.argv[1] == "change":
      print("call function change")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      change(ipadd,port,jid)
      os.system('logger -t montag -p user.info Sending Rainbow Notification')
      sys.exit(0)
if sys.argv[1] == "retire":
      print("call function retire")
      os.system('logger -t montag -p user.info MAC SEC Script - Variable received from rsyslog ' + sys.argv[1])
      retire(ipadd,port,ip,jid)
      os.system('logger -t montag -p user.info MAC SEC Script - Sending Rainbow Notification')
      collect_log(ip)
      os.system('logger -t montag -p user.info MAC SEC Script - Sending Attachment on Rainbow')
      sys.exit(0)

else:
      os.system('logger -t montag -p user.info Wrong parameter received ' + sys.argv[1])
      sys.exit(2)

### stop process ###
sys.exit(0)
