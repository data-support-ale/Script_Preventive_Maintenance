#!/usr/bin/env python

import sys
import os
import json
from support_tools_OmniSwitch import get_credentials, detect_port_loop, replace_logtemp, disable_port, debugging, check_timestamp
from time import strftime, localtime, sleep
import re #Regex
from support_send_notification import send_message,send_file
from support_response_handler import request_handler_rainbow

#Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

#Get informations from logs.
switch_user,switch_password,mails,jid,ip_server,login_AP,pass_AP,tech_pass,random_id,company = get_credentials()

# Log sample OS6860E swlogd bcmd rpcs DBG2: slnHwlrnCbkHandler:648 port 19 mod 0 auth 0 group 0
last = ""
with open("/var/log/devices/lastlog_loop.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_loop.json","w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_loop.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_loop.json empty")
        exit()

    port,slot = re.findall(r"port (.*?) mod (.*?) auth", msg)[0]

if check_timestamp()>15: # if the last log has been recieved less than 10 seconds ago :
   if  detect_port_loop(): # if there is more than 10 log with less of 2 seconds apart:
      print("call function disable port")
      replace_logtemp()
      subject = "A loop was detected on your OmniSwitch!"
      if jid !='':
         info = "A loop has been detected on your network from the port {0} on device {1}. (if you click on Yes, the following action will be done: Port Admin Down)".format(port, ipadd)
         answer = request_handler_rainbow(ipadd,'0',port,'0',info,jid,ip_server,random_id,"loop") #new method

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
       open('/var/log/devices/lastlog_loop.json','w').close()


