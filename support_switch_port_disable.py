#!/usr/bin/env python

import sys
import os
import getopt
import json
import logging
import subprocess
from support_tools_OmniSwitch import get_credentials
from time import gmtime, strftime, localtime, sleep
import re #Regex
from support_send_notification import send_message, send_mail,send_file
from support_response_handler import request_handler_mail,request_handler_rainbow,request_handler_both

#Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

#Get informations from logs.
switch_user, switch_password, jid, gmail_user, gmail_password, mails, ip_server_log = get_credentials()
ip_switch, portnumber = extract_ip_port("loop")





if check_timestamp()>15: # if the last log has been recieved less than 10 seconds ago :
   if  detect_port_loop(): # if there is more than 10 log with less of 2 seconds apart:
      print("call function disable port")
      replace_logtemp()
      id_client = get_id_client()
      subject = "A loop was detected on your OmniSwitch!"
      if gmail_user !='' and jid !='':
         info = "A loop has been detected on your network from the port {0} on device {1}. (if you click on Yes, the following action will be done: Port Admin Down)".format(portnumber, ip_switch)
         answer = request_handler_both(ip_switch,'0',portnumber,'0',info,subject,gmail_user,gmail_password,mails,jid,ip_server_log,id_client,"loop")
      elif gmail_user !='':
         info = "A loop has been detected on your network from the port {0} on device {1}. (if you click on Yes, the following action will be done: Port Admin Down)".format(portnumber, ip_switch)
         answer = request_handler_mail(ip_switch,'0',portnumber,'0',info,subject,gmail_user,gmail_password,mails,ip_server_log,id_client,"loop") #new method
      elif jid !='':
         info = "A loop has been detected on your network from the port {0} on device {1}. (if you click on Yes, the following action will be done: Port Admin Down)".format(portnumber, ip_switch)
         answer = request_handler_rainbow(ip_switch,'0',portnumber,'0',info,jid,ip_server_log,id_client,"loop") #new method

      else :
         answer = '1'
      if answer == '1':
            disable_port(switch_user,switch_password,ip_switch,portnumber)
            os.system('logger -t montag -p user.info Process terminated')
            if jid !='':
              info = "Log of device : {0}".format(ip_switch)
              send_file(info,jid,ip_switch)
              info = "A loop has been detected on your network and the port {0} is administratively disabled on device {1}".format(portnumber, ip_switch)
              send_message(info,jid)

            disable_debugging(switch_user,switch_password,ip_switch)
            #clear lastlog file
            sleep(1)
            open('/var/log/devices/lastlog_loop.json','w').close()
      else:
         print("Mail request set as no")
         os.system('logger -t montag -p user.info Mail request set as no')
         sleep(1)
         open('/var/log/devices/lastlog_loop.json','w').close()

else:
       print("logs are too close")
       os.system('logger -t montag -p user.info Logs are too close')
       # clear lastlog file
       open('/var/log/devices/lastlog_loop.json','w').close()


