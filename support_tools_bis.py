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
def ssh_connectivity_check(ipadd,cmd):
  """ 
  This function takes entry the command to push remotely on OmniSwitch by SSH with Python Paramiko module
  Paramiko exceptions are handled for notifying Network Administrator if the SSH Session does not establish

  :param str ipadd                  Command pushed by SSH on OmnISwitch
  :param str cmd                    Switch IP address
  :return:  stdout, stderr          If exceptions is returned on stderr a notification is sent to Network Administrator, else we log the session was established
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
def debugging(appid_1,subapp_1,level_1):
    """ 
    This function takes entries arguments the appid, subapp and level to apply on switch for enabling or disabling debug logs

    :param str appid_1:               swlog appid function (ipv4,bcmd)
    :param str subapp_1:              swlog subapp component (all)
    :param str level_1:               swlog debug level (debug1,debug2,debug3,info)
    :script executed ssh_device:      with cmd in argument
    :return:                          None
    """

    cmd = ("swlog appid {0} subapp {1} level {2}").format(appid_1,subapp_1,level_1)
    ssh_device(cmd)

### Function to collect PMD file by SFTP when Core Dump is noticed
def get_pmd_sftp(host,ipadd,filename_pmd):
  """ 
  This function takes entries arguments the Path of Core Dump file.
  This function returns file path containing the pmd file and the notification subject, body used when calling VNA API

  :param str filename_pmd:                Path of Core Dump file (e.g. /flash/pmd/pmd-agCmm-11.24.2021-06.33.20)
  :param str host:                        Switch Hostname
  :param str ipadd:                       Switch IP address
  :return:                                filename_path,subject,action,result,category
  """
  date = datetime.date.today()
  pmd_file = filename_pmd.replace("/", "_")
  with pysftp.Connection(host=ipadd, username=switch_user, password=switch_password) as sftp:
      sftp.get('{0}'.format(filename_pmd), '/tftpboot/{0}_{1}_{2}'.format(date,ipadd,pmd_file))         # get a remote file
  filename_path = '/tftpboot/{0}_{1}_{2}'.format(date,ipadd,pmd_file)
  subject = ("Preventive Maintenance Application - Core dump noticed on switch: {0}").format(ipadd)
  action = ("The PMD file {0} is collected from OmniSwitch (Hostname: {1})").format(filename_path,host)
  result= "Find enclosed to this notification the pmd file"
  category = "core_dump"
  return filename_path,subject,action,result,category

### Function to collect tech_support_complete.tar file by SFTP
def get_tech_support_sftp(host,ipadd):
  """ 
  This function takes entries arguments the OmniSwitch IP Address
  This function returns file path containing the tech_support_complete file and the notification subject, body used when calling VNA API

  :param str host:                        Switch Hostname
  :param str ipadd:                       Switch IP address
  :return:                                filename_path,subject,action,result,category
  """
  date = datetime.date.today()
  date_hm = datetime.datetime.today()
  filename = 'tech_support_complete.tar'
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
        sys.exit(2)

  filename= "/tftpboot/{0}_{1}-{2}_{3}_{4}".format(date,date_hm.hour,date_hm.minute,ipadd,filename)

  with pysftp.Connection(host=ipadd, username=user, password=password) as sftp:
      sftp.get('./{0}'.format(filename), '/tftpboot/{0}_{1}-{2}_{3}_{4}'.format(date,date_hm.hour,date_hm.minute,ipadd,filename))
  subject = ("Preventive Maintenance Application - Show Tech-Support Complete command executed on switch: {0}").format(ipadd)
  action = ("The Show Tech-Support Complete file {0} is collected from OmniSwitch (Hostname: {1})").format(filename_path,host)
  result= "Find enclosed to this notification the tech_support_complete.tar file"
  category = "tech_support_complete"
  return filename_path,subject,action,result,category

### Function to collect several command outputs related to TCAM failure
def collect_command_output_tcam(host,ipadd):
  """ 
  This function takes entries arguments the OmniSwitch IP Address where TCAM (QOS) failure is noticed.
  This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

  :param str host:                  Switch Hostname
  :param str ipadd:                 Switch IP address
  :return:                          filename_path,subject,action,result,category
  """
  text = "More logs about the switch : {0} \n\n\n".format(ipadd)

  l_switch_cmd = []
  l_switch_cmd.append("show qos config")
  l_switch_cmd.append("show qos statistics")
  l_switch_cmd.append("show qos log")
  l_switch_cmd.append("show qos rules")
  l_switch_cmd.append("show tcam utilization detail")

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
  subject = ("Preventive Maintenance Application - A TCAM failure (QOS) is noticed on switch: {0}, reason {1}").format(ipadd,source)
  action = ("A TCAM failure (QOS) is noticed on OmniSwitch (Hostname: {0})").format(host)
  result= "Find enclosed to this notification the log collection of command outputs"
  category = "qos"
  return filename_path,subject,action,result,category

### Function to collect several command outputs related to Cloud-Agent (OV Cirrus) failure
def collect_command_output_ovc(decision,host,ipadd):
  """ 
  This function takes entries arguments the OmniSwitch IP Address where cloud-agent is enabled
  This function checks the decision received from Admin:
     if decision is 1, Administrator selected Yes and script disables the Cloud-Agent feature
     if decision is 0, Administrator selected No and we only provide command outputs  
  This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

  :param int desicion:              Administrator decision (1: 'Yes', 0: 'No')
  :param str host:                  Switch Hostname
  :param str ipadd:                 Switch IP address
  :return:                          filename_path,subject,action,result,category
  """
  text = "More logs about the switch : {0} \n\n\n".format(ipadd)

  l_switch_cmd = []
  l_switch_cmd.append("show cloud-agent status")
  if decision == "1":
      l_switch_cmd.append("cloud-agent admin-state disable force")
      l_switch_cmd.append("show cloud-agent status")

  for switch_cmd in l_switch_cmd:
     cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password,switch_user,ipadd,switch_cmd)
     output=subprocess.check_output(cmd,stderr=subprocess.DEVNULL, shell=True)
     output=output.decode('UTF-8').strip()
     text = "{0}{1}: \n{2}\n\n".format(text,switch_cmd,output)

  date = datetime.date.today()
  date_hm = datetime.datetime.today()

  filename= "{0}_{1}-{2}_{3}_ovc_logs".format(date,date_hm.hour,date_hm.minute,ipadd)
  filename_path= ('/opt/ALE_Script/{0}.txt').format(filename)
  f_logs = open(filename_path,'w')
  f_logs.write(text)
  f_logs.close()
  subject = ("Preventive Maintenance Application - Cloud-Agent module is into Invalid Status on OmniSwitch {0}").format(host)
  if decision == "1":
      action = ("The Cloud Agent feature is administratively disabled on OmniSwitch (Hostname: {0})").format(host)
      result= "Find enclosed to this notification the log collection of actions done"
  else:
      action = ("No action done on OmniSwitch (Hostname: {0}), please ensure the Serial Number is added in the OV Cirrus Device Catalog").format(host)      
      result= "Find enclosed to this notification the log collection"
  category = "ovc"
  return filename_path,subject,action,result,category

### Function to collect several command outputs related to MQTT failure
def collect_command_output_mqtt(ovip,decision,host,ipadd):
  """ 
  This function takes entries arguments the OmniVista IP Address used for Device Profiling
  This function checks the decision received from Admin:
     if decision is 1, Administrator selected Yes and script disables the Device Profiling
     if decision is 0, Administrator selected No and we only provide command outputs  
  This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

  :param str ovip:                  OmniVista IP Address (e.g. 143.209.0.2:1883)
  :param int desicion:              Administrator decision (1: 'Yes', 0: 'No')
  :param str host:                  Switch Hostname
  :param str ipadd:                 Switch IP address
  :return:                          filename_path,subject,action,result,category
  """
  text = "More logs about the switch : {0} \n\n\n".format(ipadd)

  l_switch_cmd = []
  l_switch_cmd.append("show device-profile config")
  l_switch_cmd.append("show appmgr iot-profiler")
  if decision == "1":
      l_switch_cmd.append("device-profile admin-state disable")
      l_switch_cmd.append("show device-profile config")
      l_switch_cmd.append("show appmgr iot-profiler")

  for switch_cmd in l_switch_cmd:
     cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password,switch_user,ipadd,switch_cmd)
     output=subprocess.check_output(cmd,stderr=subprocess.DEVNULL, shell=True)
     output=output.decode('UTF-8').strip()
     text = "{0}{1}: \n{2}\n\n".format(text,switch_cmd,output)

  date = datetime.date.today()
  date_hm = datetime.datetime.today()

  filename= "{0}_{1}-{2}_{3}_mqtt_logs".format(date,date_hm.hour,date_hm.minute,ipadd)
  filename_path= ('/opt/ALE_Script/{0}.txt').format(filename)
  f_logs = open(filename_path,'w')
  f_logs.write(text)
  f_logs.close()
  subject = ("Preventive Maintenance Application - Device Profiling (aka IoT Profiling)  module is enabled on OmniSwitch {0} but is not able to connect to OmniVista IP Address: {1}").format(host,ovip)
  if decision == "1":
      action = ("The Device Profiling feature is administratively disabled on OmniSwitch (Hostname: {0})").format(host)
      result= "Find enclosed to this notification the log collection of actions done"
  else:
      action = ("No action done on OmniSwitch (Hostname: {0})").format(host)      
      result= "Find enclosed to this notification the log collection"
  category = "mqtt"
  return filename_path,subject,action,result,category

### Function to collect several command outputs related to Unexpected traffic (storm) detected
def collect_command_output_storm(port,source,decision,host,ipadd):
  """ 
  This function takes entries arguments the Interface/Port where storm occurs and the type of traffic. 
  This function checks the decision received from Admin:
     if decision is 1, Administrator selected Yes and script disables the interface
     if decision is 0, Administrator selected No and we only provide command outputs  
  This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

  :param str port:                  Switch Interface/Port ID <chasis>/<slot>/>port>
  :param str source:                Switch Traffic type (broadcast, multicast, unknown unicast)
  :param int desicion:              Administrator decision (1: 'Yes', 0: 'No')
  :param str host:                  Switch Hostname
  :param str ipadd:                 Switch IP address
  :return:                          filename_path,subject,action,result,category
  """
  text = "More logs about the switch : {0} \n\n\n".format(ipadd)

  l_switch_cmd = []
  l_switch_cmd.append("show interfaces " + port +" status")
  l_switch_cmd.append("show interfaces " + port +" counters")
  l_switch_cmd.append("show interfaces " + port +" flood-rate")
  if decision == "1":
      l_switch_cmd.append("interfaces port " + port +" admin-state disable")
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

  filename= "{0}_{1}-{2}_{3}_storm_logs".format(date,date_hm.hour,date_hm.minute,ipadd)
  filename_path= ('/opt/ALE_Script/{0}.txt').format(filename)
  f_logs = open(filename_path,'w')
  f_logs.write(text)
  f_logs.close()
  subject = ("Preventive Maintenance Application - Unexpected traffic (storm) detected on switch: {0}, reason {1}").format(ipadd,source)
  if decision == "1":
      action = ("The Port {0} is administratively disabled on OmniSwitch (Hostname: {1})").format(port,host)
      result= "Find enclosed to this notification the log collection of actions done"
  else:
      action = ("No action done on OmniSwitch (Hostname: {0})").format(host)      
      result= "Find enclosed to this notification the log collection"
  category = "storm"
  return filename_path,subject,action,result,category

### Function to collect several command outputs related to Port Violation
def collect_command_output_violation(port,source,decision,host,ipadd):
  """ 
  This function takes entries arguments the Interface/Port where violation occurs. 
  This function checks the decision received from Admin:
     if decision is 1, Administrator selected Yes and script clears the violation
     if decision is 0, Administrator selected No and we only provide command outputs
  This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

  :param str port:                  Switch Interface/Port ID <chasis>/<slot>/>port>
  :param str source:                Switch Violation reason (lbd, Access Guardian, lps)
  :param int desicion:              Administrator decision (1: 'Yes', 0: 'No')
  :param str host:                  Switch Hostname
  :param str ipadd:                 Switch IP address
  :return:                          filename_path,subject,action,result,category
  """
  text = "More logs about the switch : {0} \n\n\n".format(ipadd)

  l_switch_cmd = []
  l_switch_cmd.append("show interfaces " + port +" status")
  if decision == "1":
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

  filename= "{0}_{1}-{2}_{3}_violation_logs".format(date,date_hm.hour,date_hm.minute,ipadd)
  filename_path= ('/opt/ALE_Script/{0}.txt').format(filename)
  f_logs = open(filename_path,'w')
  f_logs.write(text)
  f_logs.close()
  subject = ("Preventive Maintenance Application - Port violation noticed on switch: {0}, reason {1}").format(ipadd,source)
  if decision == "1":
      action = ("The Port {0} is cleared from violation table on OmniSwitch (Hostname: {1})").format(port,host)
      result= "Find enclosed to this notification the log collection of actions done"
  else:
      action = ("No action done on OmniSwitch (Hostname: {0})").format(host)      
      result= "Find enclosed to this notification the log collection"   
  result= "Find enclosed to this notification the log collection of actions done"
  category = "violation"
  return filename_path,subject,action,result,category

### Function to collect several command outputs related to SPB issue
def collect_command_output_spb(host,ipadd):
  """ 
  This function takes entries arguments the OmniSwitch IP Address
  This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

  :param str host:                  Switch Hostname
  :param str ipadd:                 Switch IP address
  :return:                          filename_path,subject,action,result,category
  """
  text = "More logs about the switch : {0} \n\n\n".format(ipadd)

  l_switch_cmd = []
  l_switch_cmd.append("show spb isis adjacency")
  l_switch_cmd.append("show spb isis interface")

  for switch_cmd in l_switch_cmd:
     cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password,switch_user,ipadd,switch_cmd)
     output=subprocess.check_output(cmd,stderr=subprocess.DEVNULL, shell=True)
     output=output.decode('UTF-8').strip()
     text = "{0}{1}: \n{2}\n\n".format(text,switch_cmd,output)

  date = datetime.date.today()
  date_hm = datetime.datetime.today()

  filename= "{0}_{1}-{2}_{3}_spb_logs".format(date,date_hm.hour,date_hm.minute,ipadd)
  filename_path= ('/opt/ALE_Script/{0}.txt').format(filename)
  f_logs = open(filename_path,'w')
  f_logs.write(text)
  f_logs.close()
  subject = ("Preventive Maintenance Application - SPB Adjacency issue detected on switch: {0}").format(ipadd)
  action = ("A SPB adjacency is down on OmniSwitch (Hostname: {0})").format(host)
  result= "Find enclosed to this notification the log collection for further analysis"
  category = "spb"
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

  filename= "{0}_{1}-{2}_{3}_ps_logs".format(date,date_hm.hour,date_hm.minute,ipadd)
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
ssh_connectivity_check(ipadd,cmd)
#filename_path,subject,action,result,category = collect_command_output_poe(host,ipadd)
#send_file(filename_path,subject,action,result)
agg = "6"
#filename_path,subject,action,result,category = collect_command_output_linkagg(agg,host,ipadd)
#send_file(filename_path,subject,action,result)
vcid="2"
#filename_path,subject,action,result,category = collect_command_output_vc(vcid,host,ipadd)
#send_file(filename_path,subject,action,result)
psid = "2"
#filename_path,subject,action,result,category = collect_command_output_ps(psid,host,ipadd)
#send_file(filename_path,subject,action,result)
source="Access Guardian"
port="1/1/1"
decision="0"
filename_path,subject,action,result,category = collect_command_output_violation(port,source,decision,host,ipadd)
send_file(filename_path,subject,action,result)
filename_path,subject,action,result,category = collect_command_output_storm(port,source,decision,host,ipadd)
send_file(filename_path,subject,action,result)
