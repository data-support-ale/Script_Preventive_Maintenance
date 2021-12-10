#!/usr/bin/env python3

import sys
import os
import getopt
import json
import logging
import datetime
from time import gmtime, strftime, localtime,sleep
from support_tools import get_credentials,get_server_log_ip,get_jid,get_mail,send_python_file_sftp,get_file_sftp
from support_send_notification import send_message,send_file,send_mail,send_message_aijaz
import subprocess
import re
import pysftp
import requests
import paramiko

##This script contains all functions interacting with OmniSwitches

### Function SSH for checking connectivity before collecting logs
def ssh_connectivity_check(cmd):
  """ 
  This function takes entry the command to push remotely on OmniSwitch by SSH with Python Paramiko module
  Paramiko exceptions are handled for notifying Network Administrator if the SSH Session does not establish

  :param str cmd                  Command pushed by SSH on OmnISwitch
  :return:  stdout, stderr        If exceptions is returned on stderr a notification is sent to Network Administrator, else we log the session was established
  """
  print(cmd)
  try:
     p = paramiko.SSHClient()
     p.set_missing_host_key_policy(paramiko.AutoAddPolicy())
     p.connect(ipadd, port=22, username=switch_user, password=switch_password)
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
  stdin, stdout, stderr = p.exec_command(cmd)
  exception = stderr.readlines()
  exception = str(exception)
  connection_status = stdout.channel.recv_exit_status()
  if connection_status != 0:
     info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd,exception)
     send_message(info,jid)
     os.system('logger -t montag -p user.info ' + info)
     sys.exit(2)
  else:
      info = ("SSH Session established successfully on OmniSwitch {0}").format(ipadd)
      os.system('logger -t montag -p user.info ' + info)

### Function debug
def debugging(user,password,ipadd,appid_1,subapp_1,level_1):
    """ 
    This function takes entries arguments the appid, subapp and level to apply on switch for enabling or disabling debug logs

    :param str user:                  Switch user login
    :param str password:              Switch user password
    :param str ipadd:                 Switch IP Address
    :param str appid_1:               swlog appid function (ipv4,bcmd)
    :param str subapp_1:              swlog subapp component (all)
    :param str level_1:               swlog debug level (debug1,debug2,debug3,info)
    :script executed ssh_device:      with cmd in argument
    :return:                          None
    """

    cmd = ("swlog appid {0} subapp {1} level {2}").format(appid_1,subapp_1,level_1)
    ssh_device(cmd)

### Function to collect several command outputs related to Power Supply
def collect_command_output_violation(port,source,host,ipadd):
  """ 
  This function takes entries arguments the Interface/Port where violation occurs. This function is called when is port is put into violation and Administrator wants to clear the violation
  This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

  :param str port:                  Switch Interface/Port ID <chasis>/<slot>/>port>
  :param str source:                Switch Violation reason (lbd, Access Guardian, lps)
  :param str host:                  Switch Hostname
  :param str ipadd:                 Switch IP address
  :return:                          filename_path,subject,action,result,category
  """
  text = "More logs about the switch : {0} \n\n\n".format(ipadd)

  l_switch_cmd = []
  l_switch_cmd.append("show interfaces " + port +" status")
  l_switch_cmd.append("clear violation port " + port)
  l_switch_cmd.append("show violation")
  l_switch_cmd.append("show violation port "  + port)

  for switch_cmd in l_switch_cmd:
     cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password,switch_user,ipadd,switch_cmd)
     output=subprocess.check_output(cmd,stderr=subprocess.DEVNULL, shell=True)
     output=output.decode('UTF-8').strip()
     text = "{0}{1}: \n{2}\n\n".format(text,switch_cmd,output)

  date = datetime.date.today()
  date_hm = datetime.datetime.today()

  filename= "{0}_{1}-{2}_{3}_vcmm_logs".format(date,date_hm.hour,date_hm.minute,ipadd)
  filename_path= ('/opt/ALE_Script/{0}.txt').format(filename)
  f_logs = open(filename_path,'w')
  f_logs.write(text)
  f_logs.close()
  subject = ("Preventive Maintenance Application - Port violation noticed on switch: {0}, reason {1}").format(ipadd,source)
  action = ("The Port {0} is cleared from violation table on OmniSwitch (Hostname: {1})").format(psid,host)
  result= "Find enclosed to this notification the log collection of actions done"
  category = "violation"
  return filename_path,subject,action,result,category

### Function to collect several command outputs related to Power Supply
def collect_command_output_ps(psid,host,ipadd):
  """ 
  This function takes entries arguments the Power Supply ID. This function is called when an issue is observed on Power Supply hardware
  This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

  :param str psid:                  Switch Power Supply ID
  :param str host:                  Switch Hostname
  :param str ipadd:                 Switch IP address
  :return:                          filename_path,subject,action,result,category
  """
  text = "More logs about the switch : {0} \n\n\n".format(ipadd)

  l_switch_cmd = []
  l_switch_cmd.append("show powersupply")
  l_switch_cmd.append("show powersupply total")

  for switch_cmd in l_switch_cmd:
     cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password,switch_user,ipadd,switch_cmd)
     output=subprocess.check_output(cmd,stderr=subprocess.DEVNULL, shell=True)
     output=output.decode('UTF-8').strip()
     text = "{0}{1}: \n{2}\n\n".format(text,switch_cmd,output)

  date = datetime.date.today()
  date_hm = datetime.datetime.today()

  filename= "{0}_{1}-{2}_{3}_vcmm_logs".format(date,date_hm.hour,date_hm.minute,ipadd)
  filename_path= ('/opt/ALE_Script/{0}.txt').format(filename)
  f_logs = open(filename_path,'w')
  f_logs.write(text)
  f_logs.close()
  subject = ("Preventive Maintenance Application - Power Supply issue detected on switch: {0}").format(ipadd)
  action = ("The Power Supply unit {0} is down or running abnormal on OmniSwitch (Hostname: {1})").format(psid,host)
  result= "Find enclosed to this notification the log collection for further analysis"
  category = "ps"
  return filename_path,subject,action,result,category

### Function to collect several command outputs related to Virtual Chassis
def collect_command_output_vc(vcid,host,ipadd):
  """ 
  This function takes entries arguments the Virtual Chassis ID and the Switch System Name. This function is called when an issue is observed on Virtual Chassis category
  This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

  :param str vcid:                  Switch Virtual Chassis ID
  :param str host:                  Switch Hostname
  :param str ipadd:                 Switch IP address
  :return:                          filename_path,subject,action,result,category
  """
  text = "More logs about the switch : {0} \n\n\n".format(ipadd)

  l_switch_cmd = []
  l_switch_cmd.append("show virtual-chassis vf-link")
  l_switch_cmd.append("show virtual-chassis auto-vf-link-port")
  l_switch_cmd.append("show virtual-chassis neighbors")
  l_switch_cmd.append("debug show virtual-chassis topology")

  for switch_cmd in l_switch_cmd:
     cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password,switch_user,ipadd,switch_cmd)
     output=subprocess.check_output(cmd,stderr=subprocess.DEVNULL, shell=True)
     output=output.decode('UTF-8').strip()
     text = "{0}{1}: \n{2}\n\n".format(text,switch_cmd,output)

  date = datetime.date.today()
  date_hm = datetime.datetime.today()

  filename= "{0}_{1}-{2}_{3}_vcmm_logs".format(date,date_hm.hour,date_hm.minute,ipadd)
  filename_path= ('/opt/ALE_Script/{0}.txt').format(filename)
  f_logs = open(filename_path,'w')
  f_logs.write(text)
  f_logs.close()
  subject = ("Preventive Maintenance Application - Virtual Chassis issue detected on switch: {0}").format(ipadd)
  action = ("The VC CMM {0} is down on VC (Hostname: {1}) syslogs").format(vcid,host)
  result= "Find enclosed to this notification the log collection for further analysis"
  category = "vcmm"
  return filename_path,subject,action,result,category

### Function to collect several command outputs related to Linkagg
def collect_command_output_linkagg(agg,host,ipadd):
  """ 
  This function takes entries arguments the Link Aggregation ID. This function is called when an issue is observed on Linkagg category
  This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

  :param str agg:                   Link Aggregation ID
  :param str host:                  Switch Hostname
  :param str ipadd:                 Switch IP address
  :return:                          filename_path,subject,action,result,category
  """
  text = "More logs about the switch : {0} \n\n\n".format(ipadd)

  l_switch_cmd = []
  l_switch_cmd.append("show interfaces alias")
  l_switch_cmd.append("show linkagg")
  l_switch_cmd.append("show linkagg agg " + agg)
  l_switch_cmd.append("show linkagg agg " + agg + " port")

  for switch_cmd in l_switch_cmd:
     cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password,switch_user,ipadd,switch_cmd)
     output=subprocess.check_output(cmd,stderr=subprocess.DEVNULL, shell=True)
     output=output.decode('UTF-8').strip()
     text = "{0}{1}: \n{2}\n\n".format(text,switch_cmd,output)

  date = datetime.date.today()
  date_hm = datetime.datetime.today()

  filename= "{0}_{1}-{2}_{3}_linkagg_logs".format(date,date_hm.hour,date_hm.minute,ipadd)
  filename_path= ('/opt/ALE_Script/{0}.txt').format(filename)
  f_logs = open(filename_path,'w')
  f_logs.write(text)
  f_logs.close()
  subject = ("Preventive Maintenance Application - Linkagg issue detected on switch: {0}").format(ipadd)
  action = ("A Linkagg issue has been detected in switch(Hostname: {0}) Aggregate {1}").format(host,agg)
  result= "Find enclosed to this notification the log collection for further analysis"
  category = "linkagg"
  return filename_path,subject,action,result,category

### Function to collect several command outputs related to PoE
def collect_command_output_poe(host,ipadd):
  """ 
  This function takes IP Address and Hostname as argument. This function is called when an issue is observed on Lanpower category
  This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API
  :param str host:                  Switch Hostname
  :param str ipadd:                 Switch IP address
  :return:                          filename_path,subject,action,result,category
  """
  text = "More logs about the switch : {0} \n\n\n".format(ipadd)

  l_switch_cmd = []
  l_switch_cmd.append("show interfaces alias")
  l_switch_cmd.append("show system")
  l_switch_cmd.append("show date")
  l_switch_cmd.append("show lldp remote-system")
  l_switch_cmd.append("show configuration snapshot lanpower")
  l_switch_cmd.append("show powersupply total")
  l_switch_cmd.append("show lanpower slot 1/1")
  l_switch_cmd.append("show lanpower slot 2/1")
  l_switch_cmd.append("show lanpower slot 3/1")
  l_switch_cmd.append("show lanpower power-rule")
  l_switch_cmd.append("show lanpower chassis 1 capacitor-detection")
  l_switch_cmd.append("show lanpower chassis 2 capacitor-detection")
  l_switch_cmd.append("show lanpower chassis 3 capacitor-detection")
  l_switch_cmd.append("show lanpower chassis 1 usage-threshold")
  l_switch_cmd.append("show lanpower chassis 2 usage-threshold")
  l_switch_cmd.append("show lanpower chassis 3 usage-threshold")
  l_switch_cmd.append("show lanpower chassis 1 ni-priority")
  l_switch_cmd.append("show lanpower chassis 2 ni-priority")
  l_switch_cmd.append("show lanpower chassis 3 ni-priority")
  l_switch_cmd.append("show lanpower slot 1/1 high-resistance-detection")
  l_switch_cmd.append("show lanpower slot 2/1 high-resistance-detection")
  l_switch_cmd.append("show lanpower slot 3/1 high-resistance-detection")
  l_switch_cmd.append("show lanpower slot 1/1 priority-disconnect")
  l_switch_cmd.append("show lanpower slot 2/1 priority-disconnect")
  l_switch_cmd.append("show lanpower slot 3/1 priority-disconnect")
  l_switch_cmd.append("show lanpower slot 1/1 class-detection")
  l_switch_cmd.append("show lanpower slot 2/1 class-detection")
  l_switch_cmd.append("show lanpower slot 3/1 class-detection")

  for switch_cmd in l_switch_cmd:
     cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password,switch_user,ipadd,switch_cmd)
     output=subprocess.check_output(cmd,stderr=subprocess.DEVNULL, shell=True)
     output=output.decode('UTF-8').strip()
     text = "{0}{1}: \n{2}\n\n".format(text,switch_cmd,output)

  date = datetime.date.today()
  date_hm = datetime.datetime.today()

  filename= "{0}_{1}-{2}_{3}_poe_logs".format(date,date_hm.hour,date_hm.minute,ipadd)
  filename_path= ('/opt/ALE_Script/{0}.txt').format(filename)
  f_logs = open(filename_path,'w')
  f_logs.write(text)
  f_logs.close()
  lanpower_settings_status = 0
  switch_cmd="show configuration snapshot lanpower"
  cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password,switch_user,ipadd,switch_cmd)
  lanpower_settings_status=subprocess.check_output(cmd,stderr=subprocess.DEVNULL, shell=True)
  lanpower_settings_status=lanpower_settings_status.decode('UTF-8').strip()
  print(lanpower_settings_status)
  if "capacitor-detection enable" in lanpower_settings_status:
     print("Capacitor detection enabled!")
     capacitor_detection_status="enabled"
  else:
      capacitor_detection_status="disabled"
  if "high-resistance-detection enable" in lanpower_settings_status:
     print("High Resistance detection enabled!")
     high_resistance_detection_status="enabled"
  else:
      high_resistance_detection_status="disabled"
  subject = ("Preventive Maintenance Application - Lanpower issue detected on switch: {0}").format(ipadd)
  action = ("A PoE issue has been detected in switch(Hostname : {0}) syslogs. Capacitor Detection is {1}, High Resistance Detection is {2}").format(host,capacitor_detection_status,high_resistance_detection_status)
  result= "Find enclosed to this notification the log collection for further analysis"
  category = "poe"
  return filename_path,subject,action,result,category

def send_file(filename_path,subject,action,result):
  """ 
  This function takes as argument the file containins command outputs, the notification subject, notification action and result. 
  This function is called for attaching file on Rainbow or Email notification
  :param str filename_path:                  Path of file attached to the notification
  :param str subject:                        Notification subject
  :param str action:                         Preventive Action done
  :param str result:                         Preventive Result
  :param int Card:                           Set to 0 for sending notification without card
  :param int Email:                          0 if email is disabled, 1 if email is enabled
  :return:                                   None
  """
  url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_File_EMEA"
  request_debug = "Call VNA REST API Method POST path %s"%url
  print(request_debug)
  os.system('logger -t montag -p user.info Call VNA REST API Method POST')
  headers = {  'Content-type':"text/plain",'Content-Disposition': ("attachment;filename={0}_troubleshooting.log").format(category), 'jid1': '{0}'.format(jid), 'tata': '{0}'.format(subject),'toto': '{0}'.format(action),'tutu': '{0}'.format(result), 'Card': '0', 'Email': '0'}
  files = {'file': open(filename_path,'r')}
  response = requests.post(url,files=files, headers=headers)
  print(response)
  response = "<Response [200]>"
  response = re.findall(r"<Response \[(.*?)\]>", response)
  if "200" in response:
     os.system('logger -t montag -p user.info 200 OK')
  else:
     os.system('logger -t montag -p user.info REST API Call Failure') 

jid = "570e12872d768e9b52a8b975@openrainbow.com"
switch_password="switch"
switch_user="admin"
ipadd="10.130.7.244"
cmd="show system"
host="LAN-6860N-2"
ssh_connectivity_check(cmd)
filename_path,subject,action,result,category = collect_command_output_poe(host,ipadd)
send_file(filename_path,subject,action,result)
agg = "6"
filename_path,subject,action,result,category = collect_command_output_linkagg(agg,host,ipadd)
send_file(filename_path,subject,action,result)
vcid="2"
filename_path,subject,action,result,category = collect_command_output_vc(vcid,host,ipadd)
send_file(filename_path,subject,action,result)
psid = "2"
filename_path,subject,action,result,category = collect_command_output_ps(psid,host,ipadd)
send_file(filename_path,subject,action,result)
source="Access Guardian"
port="1/1/1"
filename_path,subject,action,result,category = collect_command_output_violation(port,source,host,ipadd)
send_file(filename_path,subject,action,result)
