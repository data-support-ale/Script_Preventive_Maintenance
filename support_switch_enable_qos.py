#!/usr/bin/env python3

import sys
import os
import getopt
import json
import logging
import subprocess
import pysftp
from support_tools import enable_debugging, disable_debugging, disable_port, extract_ip_port, check_timestamp, get_credentials,extract_ip_ddos,disable_debugging_ddos,enable_qos_ddos,get_id_client,get_server_log_ip
from time import gmtime, strftime, localtime, sleep
from support_send_notification import send_message, send_mail,send_file
from support_response_handler import request_handler_mail,request_handler_rainbow,request_handler_both




#Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

#Get informations from logs.
switch_user, switch_password, jid, gmail_user, gmail_password, mails,ip_server = get_credentials()
ip_switch, portnumber = extract_ip_port("qos_ddos")
ip_server_log = get_server_log_ip()
ipadd_ddos= extract_ip_ddos()
if ipadd_ddos == '0' :
   # clear lastlog file
   open('/var/log/devices/lastlog_ddos_ip.json','w').close

elif ipadd_ddos == '1' :
   os.system('logger -t montag -p user.info not enough logs')

else:

      id_client = get_id_client()
      subject = "A port scan has been detected on your network "
      if gmail_user !='' and jid !='':
         info = "A port scan has been detected on your network by the IP Address {0}  on device {1}. (if you click on Yes, the following actions will be done: Policy action block)".format(ipadd_ddos, ip_switch)
         answer = request_handler_both(ip_switch,'0',portnumber,'0',info,subject,gmail_user,gmail_password,mails,jid,ip_server_log,id_client,"ddos")
      elif gmail_user !='':
         info = "A port scan has been detected on your network by the IP Address {0}  on device {1}. (if you click on Yes, the following actions will be done: Policy action block)".format(ipadd_ddos, ip_switch)
         answer = request_handler_mail(ip_switch,'0',portnumber,'0',info,subject,gmail_user,gmail_password,mails,ip_server_log,id_client,"ddos") #new method
      elif jid !='':
         info = "A port scan has been detected on your network by the IP Address {0}  on device {1}. (if you click on Yes, the following actions will be done: Policy action block)".format(ipadd_ddos, ip_switch)
         answer = request_handler_rainbow(ip_switch,'0',portnumber,'0',info,jid,ip_server_log,id_client,"ddos") #new method

      else :
         answer = '1'
      if answer == '1':
            enable_qos_ddos(switch_user,switch_password,ip_switch,ipadd_ddos)
            os.system('logger -t montag -p user.info Process terminated')
 
            if jid !='':
              info = "Log of device : {0}".format(ip_switch)
              send_file(info,jid,ip_switch)
              info = "A port scan has been detected on your network and QOS policy has been applied to prevent access for the IP Address {0} to device {1}".format(ipadd_ddos, ip_switch)
              send_message(info,jid)
            disable_debugging_ddos(switch_user,switch_password,ip_switch)
            sleep(1)
           # clear lastlog file
            open('/var/log/devices/lastlog_ddos_ip.json','w').close


      else:
         print("Mail request set as no")
         os.system('logger -t montag -p user.info Mail request set as no')
         sleep(1)
         open('/var/log/devices/lastlog_ddos_ip.json','w').close()

