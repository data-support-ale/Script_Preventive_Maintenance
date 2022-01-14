#!/usr/bin/env python

import sys
import os
import getopt
import json
import logging
import subprocess
from time import gmtime, strftime, localtime, sleep
import requests
import datetime
import smtplib
import mimetypes
import re
from support_tools import get_credentials,get_server_log_ip,get_jid,extract_ip_port,get_mail,send_python_file_sftp,get_file_sftp
from support_send_notification import send_message,send_file,send_mail

script_name = sys.argv[0]
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

uname = os.system('uname -a')
os.system('logger -t montag -p user.info Executing script ' + script_name)

switch_user, switch_password, jid, gmail_user, gmail_password, mails,ip_server_log = get_credentials()
filename = 'tech_support_complete.tar'

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

def qos_issue(ipadd,jid):
  #ssh session to start python script remotely
  os.system('logger -t montag -p user.info PR Reference: CRAOS8X-27421 - QOS Issue reproduction ' + ipadd)
  info = "Switch: {0} - PR Reference: CRAOS8X-27421 - QOS Issue reproduction".format(ipadd)
  send_message(info,jid)

def collect_log(ipadd,jid):
  print("filename" +filename)
  cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2}  rm -rf {3}".format(switch_password,switch_user,ipadd,filename)
  run=cmd.split()
  p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)

  os.system('logger -t montag -p user.info PR Reference: CRAOS8X-27421 - show tech-support eng complete generated ' + ipadd)
  cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2}  show tech-support eng complete".format(switch_password,switch_user,ipadd)
  run=cmd.split()
  p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)

  cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2}  ls | grep {3}".format(switch_password,switch_user,ipadd,filename)
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
    out = out.decode('UTF-8').strip()
 
    if i > 20:
       print("timeout")
       exit()

  get_file_sftp(switch_user,switch_password,ipadd,filename)
  os.system('logger -t montag -p user.info PR Reference: CRAOS8X-27421 - logs sent ' + ipadd)

  if jid !='':
         info = "PR Reference: CRAOS8X-27421 - QOS Issue reproduction (IP : {0}) syslogs. A snapshot has been sent in the directory /tftpboot/ on syslog server".format(ipadd)
         send_file(info,jid,ipadd)
         send_message(info,jid)

def more_log(ipadd,jid):
  ##########################Get More LOGS########################################
  text = "More logs about the switch : {0} \n\n\n".format(ipadd)

  l_switch_cmd = []
  l_switch_cmd.append("show unp user ; show qos statistics | grep \"Spoofed Events\"")
  l_switch_cmd.append("show system | grep Time ")

  i = 1
  while i < 12:
    for switch_cmd in l_switch_cmd:
      cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password,switch_user,ipadd,switch_cmd)
      run=cmd.split()
      p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
      out, err = p.communicate()
      out=out.decode('UTF-8').strip()
      i += 1
      sleep(2.5)
      text = "{0}{1}: \n{2}\n\n".format(text,switch_cmd,out)

  date = datetime.date.today()
  date_hm = datetime.datetime.today()

  filename= "{0}_{1}-{2}_{3}_logs".format(date,date_hm.hour,date_hm.minute,ipadd)
  f_logs = open('/tftpboot/{0}.txt'.format(filename),'w')
  f_logs.write(text)
  f_logs.close()
  os.system('logger -t montag -p user.info PR Reference: CRAOS8X-27421 - File with additionnal logs created on /tftpboot/ ' + ipadd)
  if jid !='':
      info = "PR Reference: CRAOS8X-27421 - QOS Issue reproduction (IP : {0}) syslogs. Additionnal logs sent to /tftpboot/ on syslog server".format(ipadd)
#      send_file(info,jid,ipadd)
      send_message(info,jid)

def send_message(info,jid):
    """
    Send the message in info to a Rainbowbot. This bot will send this message to the jid in parameters

    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :return:                        None
    """

    print("Sending Rainbow Notification")
    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif/"
    headers = {'Content-type': 'application/json', "Accept-Charset": "UTF-8", 'jid1': '{0}'.format(jid), 'toto': '{0}'.format(info),'Card': '0'}
    response = requests.get(url, headers=headers)
    response.text


def extract_ip_port():
        content_variable = open ('/var/log/devices/lastlog_qos.json','r')
        file_lines = content_variable.readlines()
        content_variable.close()
        last_line = file_lines[-1]
        f=last_line.split(',')
        ipadd = 0
        #For each element, look if relayip is present. If yes,  separate the text and the ip address
        for element in f:
         if "relayip" in element:
           element_split = element.split(':')
           print(element_split)
           ipadd_quot = element_split[1]
           #delete quotations
           ipadd = ipadd_quot[-len(ipadd_quot)+1:-1]
           print(ipadd)
        return ipadd;


ipadd = extract_ip_port()   #returning relayIP and port number where loop detected
#jid = get_jid()
print(ipadd)
print(jid)
script_name = sys.argv[0]


if sys.argv[1] == "qos_issue":
      print("call function qos_issue")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      qos_issue(ipadd,jid)
      more_log(ipadd,jid)
      collect_log(ipadd,jid)
      os.system('logger -t montag -p user.info Sending Rainbow Notification')
      sys.exit(0)
else:
      os.system('logger -t montag -p user.info Wrong parameter received ' + sys.argv[1])
      sys.exit(2)

### stop process ###
sys.exit(0)

