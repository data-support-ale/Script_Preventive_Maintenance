#!/usr/bin/env python

import sys
import os
import getopt
import json
import logging
import subprocess
from support_tools import enable_debugging, disable_debugging, disable_port, extract_ip_port, check_timestamp, get_credentials, detect_port_flapping,enable_port,get_id_client
from support_response_handler import request_handler_both, request_handler_mail, request_handler_rainbow
from time import gmtime, strftime, localtime, sleep
import re #Regex
from support_send_notification import send_message,send_file
from database_conf import *


#Script init
script_name = sys.argv[0]
#os.system('logger -t montag -p user.info Executing script :' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

#Get informations from logs.
switch_user, switch_password, jid, gmail_user, gmail_password, mails,ip_server_log = get_credentials()
id_client = get_id_client()
subject = "A port flapping was detected in your network !"

ip_switch_1,ip_switch_2,port_switch_1,port_switch_2= detect_port_flapping()

print(ip_switch_1,ip_switch_2,port_switch_1,port_switch_2)
if not re.search(".*\/0", port_switch_1) or not re.search(".*\/0", port_switch_2): #If the portnumber is different than 0,  (not a buffer list is empty log).

    if ip_switch_1!="0" and ip_switch_2!="0": # if we get logs from 2 switches
       #request by mail or Rainbow
       if gmail_user !='' and jid !='':
          info = "A port flapping has been detected on your network on  the port {0} on device {1} and the port {2}  on device {3}. (if you click on Yes, the following actions will be done: Port Admin Down/Up)".format(port_switch_1,ip_switch_1,port_switch_2,ip_switch_2)
          answer = request_handler_both(ip_switch_1,ip_switch_2,port_switch_1,port_switch_2,info,subject,gmail_user,gmail_password,mails,jid,ip_server_log,id_client,"flapping")
       elif gmail_user !='':
          info = "A port flapping has been detected on your network on  the port {0} on device {1} and the port {2}  on device {3}. (if you click on Yes, the following actions will be done: Port Admin Down/Up)".format(port_switch_1,ip_switch_1,port_switch_2,ip_switch_2)
          answer = request_handler_mail(ip_switch_1,ip_switch_2,port_switch_1,port_switch_2,info,subject,gmail_user,gmail_password,mails,ip_server_log,id_client,"flapping")
       elif jid !='':
          info = "A port flapping has been detected on your network on  the port {0} on device {1} and the port {2}  on device {3}. (if you click on Yes, the following actions will be done: Port Admin Down/Up)".format(port_switch_1,ip_switch_1,port_switch_2,ip_switch_2)
          answer = request_handler_rainbow(ip_switch_1,ip_switch_2,port_switch_1,port_switch_2,info,jid,ip_server_log,id_client,"flapping") #new method
       else :
          answer = '1'
       if answer == '1':

         disable_port(switch_user,switch_password,ip_switch_1,port_switch_1)
         os.system('logger -t montag -p user.info Port {1} of device {0} disable'.format(ip_switch_1,port_switch_1))
         disable_port(switch_user,switch_password,ip_switch_2,port_switch_2)
         os.system('logger -t montag -p user.info Port {1} of device {0} disable'.format(ip_switch_2,port_switch_2))
         sleep(2)
         enable_port(switch_user,switch_password,ip_switch_1,port_switch_1)
         os.system('logger -t montag -p user.info Port {1} of device {0} enable'.format(ip_switch_1,port_switch_1))
         enable_port(switch_user,switch_password,ip_switch_2,port_switch_2)
         os.system('logger -t montag -p user.info Port {1} of device {0} enable'.format(ip_switch_2,port_switch_2))

         os.system('logger -t montag -p user.info Process terminated')

         if jid !='':
           info = "Log of device : {0}".format(ip_switch_1)
           send_file(info,jid,ip_switch_1)
           sleep(1)
           info = "Log of device : {0}".format(ip_switch_2)
           send_file(info,jid,ip_switch_2)
           info = "A port flapping has been detected on your network and the port {0} is administratively updated  on device {1}, the port {2}  is administratively updated  on device {3}".format(port_switch_1,ip_switch_1,port_switch_2,ip_switch_2)
           send_message(info,jid)

         disable_debugging(switch_user,switch_password,ip_switch_1)
         disable_debugging(switch_user,switch_password,ip_switch_2)
         sleep(2)
        # clear lastlog file
         open('/var/log/devices/lastlog_flapping.json','w').close()

    if ip_switch_1!="0" and ip_switch_2=="0":

       #request by mail or Rainbow
       if gmail_user !='' and jid !='':
          info = "A port flapping has been detected on your network on the port {0} from  device {1}. (if you click on Yes, the following actions will be done: Port Admin Down/Up)" .format(port_switch_1,ip_switch_1)
          answer = request_handler_both(ip_switch_1,ip_switch_2,port_switch_1,port_switch_2,info,subject,gmail_user,gmail_password,mails,jid,ip_server_log,id_client,"flapping")
       elif gmail_user !='':
          info = "A port flapping has been detected on your network on the port {0} from  device {1}. (if you click on Yes, the following actions will be done: Port Admin Down/Up)" .format(port_switch_1,ip_switch_1,)
          answer = request_handler_mail(ip_switch_1,ip_switch_2,port_switch_1,port_switch_2,info,subject,gmail_user,gmail_password,mails,ip_server_log,id_client,"flapping")
       elif jid !='':
          info = "A port flapping has been detected on your network on the port {0} from  device {1}. (if you click on Yes, the following actions will be done: Port Admin Down/Up)" .format(port_switch_1,ip_switch_1) 
          answer = request_handler_rainbow(ip_switch_1,ip_switch_2,port_switch_1,port_switch_2,info,jid,ip_server_log,id_client,"flapping") #new method
       else :
          answer = '1' #if there is no rainbow nor mail
       if answer == '1':

          disable_port(switch_user,switch_password,ip_switch_1,port_switch_1)
          os.system('logger -t montag -p user.info Port {1} of device {0} disable'.format(ip_switch_1,port_switch_1))

          sleep(2)
          enable_port(switch_user,switch_password,ip_switch_1,port_switch_1)
          os.system('logger -t montag -p user.info Port {1} of device {0} enable'.format(ip_switch_1,port_switch_1))

          os.system('logger -t montag -p user.info Process terminated')

          if jid !='':
             info = "Log of device : {0}".format(ip_switch_1)
             send_file(info,jid,ip_switch_1)
             info = "A port flapping has been detected on your network and the port {0} is administratively updated  on device {1}." .format(port_switch_1,ip_switch_1)
             send_message(info,jid)

          disable_debugging(switch_user,switch_password,ip_switch_1)
          sleep(2)
         # clear lastlog file
          open('/var/log/devices/lastlog_flapping.json','w').close()




    if ip_switch_1=="0" and ip_switch_2!="0":

       if gmail_user !='' and jid !='':
          info = "A port flapping has been detected on your network on the port {0} from  device {1}. (if you click on Yes, the following actions will be done: Port Admin Down/Up)" .format(port_switch_2,ip_switch_2)
          answer = request_handler_both(ip_switch_1,ip_switch_2,port_switch_1,port_switch_2,info,subject,gmail_user,gmail_password,mails,jid,ip_server_log,id_client,"flapping")
       elif gmail_user !='':
          info = "A port flapping has been detected on your network on the port {0} from  device {1}. (if you click on Yes, the following actions will be done: Port Admin Down/Up)" .format(port_switch_2,ip_switch_2)
          answer = request_handler_mail(ip_switch_1,ip_switch_2,port_switch_1,port_switch_2,info,subject,gmail_user,gmail_password,mails,ip_server_log,id_client,"flapping")
       elif jid !='':
          info = "A port flapping has been detected on your network on the port {0} from  device {1}. (if you click on Yes, the following actions will be done: Port Admin Down/Up)" .format(port_switch_2,ip_switch_2)
          answer = request_handler_rainbow(ip_switch_1,ip_switch_2,port_switch_1,port_switch_2,info,jid,ip_server_log,id_client,"flapping") #new method
       else :
          answer = '1' #if there is no rainbow nor mail
       if answer == '1':

          disable_port(switch_user,switch_password,ip_switch_2,port_switch_2)
          os.system('logger -t montag -p user.info Port {1} of device {0} disable'.format(ip_switch_2,port_switch_2))

          sleep(2)
          enable_port(switch_user,switch_password,ip_switch_2,port_switch_2)
          os.system('logger -t montag -p user.info Port {1} of device {0} anable'.format(ip_switch_1,port_switch_1))

          os.system('logger -t montag -p user.info Process terminated')
          if jid !='':
             info = "Log of device : {0}".format(ip_switch_2)
             send_file(info,jid,ip_switch_2)
             info = "A port flapping has been detected on your network and the port {0} is administratively updated  on device {1}" .format(port_switch_2,ip_switch_2)
             send_message(info,jid)
 

          disable_debugging(switch_user,switch_password,ip_switch_2)
          sleep(2)
          # clear lastlog file
          open('/var/log/devices/lastlog_flapping.json','w').close()