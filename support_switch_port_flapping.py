#!/usr/bin/env python

import sys
import os
import getopt
import json
import logging
import subprocess
from support_tools_OmniSwitch import get_credentials, disable_port, enable_port
from support_response_handler import request_handler_rainbow
from time import gmtime, strftime, localtime, sleep
import re #Regex
from support_send_notification import send_message,send_file
from database_conf import *


#Script init
script_name = sys.argv[0]
#os.system('logger -t montag -p user.info Executing script :' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

#Get informations from logs.
switch_user,switch_password,mails,jid,ip_server,login_AP,pass_AP,tech_pass,random_id,company = get_credentials()
subject = "A port flapping was detected in your network !"

def detect_port_flapping():
     """ 
     This function detects if there is flapping in the log.
     If there is more than 5 logs with 10 seconds apart between each, there is flapping .(10 seconds is for the demo, we can down to 1)

     :param:                                  None
     :return str first_IP:                    First switch's IP Address, if there is no flapping log on this switch, first_IP ="0"
     :return str second_IP:                   Second switch's IP Address, if there is no flapping log on this switch, second_IP ="0"
     :return str first_port:                  First switch's port, if there is no flapping log on this switch, first_port ="1/1/0"
     :return str second_port:                 Second switch's port, if there is no flapping log on this switch, second_port ="1/1/0"
     """


     #INIT VARIABLE:
     i_first_IP=0
     i_second_IP=0
     first_IP="0"
     second_IP="0"
     first_port="0"
     second_port="0"
     last_time_first_IP=0
     last_time_second_IP=0

     content_variable = open ('/var/log/devices/lastlog_flapping.json','r')
     file_lines = content_variable.readlines()
     content_variable.close()

     #for each line in the file
     print( len(file_lines))
     if not len(file_lines)>30:
        for line in file_lines:
           f=line.split(',')
           timestamp_current = f[0]
          #time in hour into decimal : #else there is en error due to second  changes 60 to 0
           current_time_split = timestamp_current[-len(timestamp_current)+26:-7].split(':')
           hour = current_time_split[0] 
           #"%02d" %  force writing on 2 digits
           minute_deci = "%02d" % int(float(current_time_split[1])*100/60)
           second_deci = "%02d" % int(float(current_time_split[2])*100/60)
           current_time = "{0}{1}{2}".format(hour,minute_deci,second_deci)
           for element in f:             #for all elements in the line :
              if "relayip" in element:
                 element_split = element.split(':')
                 ipadd_quot = element_split[1] # in the element split the ip address will always be the seconds element.
                 ipadd = ipadd_quot[-len(ipadd_quot)+1:-1]  #delete quotations
                 info = "Port flapping detected on OmniSwitch {0}".format(ipadd)
                 os.system('logger -t montag -p user.info ' + info)
                 # we need to discriminate the first ip and the second ip , if there is a third ip address we clear the file.
                 print(ipadd)
                 if first_IP=="0":
                    first_IP = ipadd
                    last_time_first_IP=current_time  # to initiate our last_time_first ip to compare to the other line ( otherwise current time is to high if last_time =0)
                 if second_IP=="0" and first_IP!= ipadd:
                    second_IP = ipadd
                    last_time_second_IP=current_time
                 if  first_IP!="0" and ipadd!=first_IP and second_IP!="0" and ipadd!=second_IP:
                         # clear lastlog file
                        open('/var/log/devices/lastlog_flapping.json','w', errors='ignore').close()


              if "LINKSTS" in element:
                 element_split = element.split()
                 for i in range(len(element_split)):
                    if element_split[i]=="LINKSTS":
                       x = element_split[i+1]
                       # TODO :looking for chassis ID number:
                       portnumber = x.replace("\\","")   #modify the format of the port number to suit the switch interface

                       if first_port=="0":
                          first_port =portnumber
                       if second_port=="0" and first_IP!= ipadd:
                          second_port = portnumber
 
              if 'DOWN' in element : #only on down log to don't make the action twice(UP/DOWN) 
                 print(current_time,last_time_first_IP,last_time_second_IP) #print for debug the script
                 print("coucou")
                 try:
                     write_api.write(bucket, org, [{"measurement": "support_switch_port_flapping.py", "tags": {"IP_Address": ipadd, "Port": portnumber}, "fields": {"count": 1}}])
                 except UnboundLocalError as error:
                     print(error)
                     sys.exit()
                 if ipadd == first_IP:
                     if (int(current_time)-int(last_time_first_IP))<10: #ten seconds for the demo, we simulate a flapping . For the real usecase we can down to 1 seconds
                        i_first_IP=i_first_IP+1     #we count how many link down 
                     last_time_first_IP = current_time

                 if ipadd == second_IP:
                    if (int(current_time)-int(last_time_second_IP))<10:
                       i_second_IP=i_second_IP+1
                    last_time_second_IP=current_time

        print(first_IP,second_IP,first_port,second_port,i_first_IP,i_second_IP)
        if i_first_IP>5 or i_second_IP>5:
           return first_IP,second_IP,first_port,second_port
        else:
           return "0","0","1/1/0","1/1/0"
     else:
        # clear lastlog file
        open('/var/log/devices/lastlog_flapping.json','w', errors='ignore').close()
        return "0","0","1/1/0","1/1/0"

ip_switch_1,ip_switch_2,port_switch_1,port_switch_2= detect_port_flapping()

print(ip_switch_1,ip_switch_2,port_switch_1,port_switch_2)
if not re.search(".*\/0", port_switch_1) or not re.search(".*\/0", port_switch_2): #If the portnumber is different than 0,  (not a buffer list is empty log).

    if ip_switch_1!="0" and ip_switch_2!="0": # if we get logs from 2 switches
       #request by mail or Rainbow
        if jid !='':
          info = "A port flapping has been detected on your network on  the port {0} on device {1} and the port {2}  on device {3}. (if you click on Yes, the following actions will be done: Port Admin Down/Up)".format(port_switch_1,ip_switch_1,port_switch_2,ip_switch_2)
          answer = request_handler_rainbow(ip_switch_1,ip_switch_2,port_switch_1,port_switch_2,info,jid,ip_server,random_id,"flapping") #new method
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
       if jid !='':
          info = "A port flapping has been detected on your network on the port {0} from  device {1}. (if you click on Yes, the following actions will be done: Port Admin Down/Up)" .format(port_switch_1,ip_switch_1) 
          answer = request_handler_rainbow(ip_switch_1,ip_switch_2,port_switch_1,port_switch_2,info,jid,ip_server,random_id,"flapping") #new method
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
       if jid !='':
          info = "A port flapping has been detected on your network on the port {0} from  device {1}. (if you click on Yes, the following actions will be done: Port Admin Down/Up)" .format(port_switch_2,ip_switch_2)
          answer = request_handler_rainbow(ip_switch_1,ip_switch_2,port_switch_1,port_switch_2,info,jid,ip_server,random_id,"flapping") #new method
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