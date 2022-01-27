#!/usr/bin/env python

import sys
import os
import json
from support_tools_OmniSwitch import get_credentials, detect_port_loop, replace_logtemp, disable_port, debugging, check_timestamp
from time import strftime, localtime, sleep
import re #Regex
from support_send_notification import send_message,send_file, send_message_request

#Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

#Get informations from logs.
switch_user,switch_password,mails,jid,ip_server,login_AP,pass_AP,tech_pass,random_id,company = get_credentials()

content_variable = open ('/var/log/devices/lastlog_loop.json','r')
file_lines = content_variable.readlines()
content_variable.close()
if len(file_lines)!=0:
    last_line = file_lines[0]
    f=last_line.split(',')
    #For each element, look if relayip is present. If yes,  separate the text and the ip address
    for element in f:
        if "relayip" in element:
            element_split = element.split(':')
            ipadd_quot = element_split[1]
            #delete quotations
            ipadd = ipadd_quot[-len(ipadd_quot)+1:-1]
            print(ipadd)
            port= 0
          #For each element, look if port is present. If yes,  we take the next element which is the port number
        if "port" in element:
            element_split = element.split()
            print(element_split)
            for i in range(len(element_split)):
               if element_split[i]=="port":
                  port = element_split[i+1]
                  slot = element_split[i+3]
                  if slot == "0":
                      slot = "1"
                  elif slot == "4":
                      slot == "2"
                  else:
                      slot == "3"
            #looking for chassis ID number:
                  port = "{0}/1/{1}".format(slot,port)   #modify the format of the port number to suit the switch interface


#if check_timestamp()>15: # if the last log has been received less than 10 seconds ago :
if  detect_port_loop(): # if there is more than 10 log with less of 2 seconds apart:
      print("call function disable port")
      replace_logtemp()
      subject = "A loop was detected on your OmniSwitch!"
      if jid !='':
         info = "A loop has been detected on your network from the port {0} on device {1}. (if you click on Yes, the following action will be done: Port Admin Down)".format(port, ipadd)
         answer = send_message_request(info,jid)

      else :
         answer = '1'
      if answer == '1':
            disable_port(switch_user,switch_password,ipadd,port)
            os.system('logger -t montag -p user.info Process terminated')
            if jid !='':
              info = "Log of device : {0}".format(ipadd)
              send_file(info,jid,ipadd)
              info = "A loop has been detected on your network and the port {0} is administratively disabled on device {1}".format(port, ipadd)
              send_message(info,jid)

            # Disable debugging logs "swlog appid bcmd subapp 3 level debug2"
            appid = "bcmd"
            subapp = "all"
            level = "info"
            # Call debugging function from support_tools_OmniSwitch 
            print("call function enable debugging")
            debugging(ipadd,appid,subapp,level)
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
#       open('/var/log/devices/lastlog_loop.json','w').close()


