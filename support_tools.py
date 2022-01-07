#!/usr/bin/env python3

import sys
import os
import getopt
import json
import logging
import subprocess
import requests
import re
from time import gmtime, strftime, localtime, sleep
from database_conf import *
import datetime
import pysftp

""" 
This script rather all the tools allowing the automation of network support tasks.
Functions allow you to retrieve switch information from the logs.
Others allow the recovery of rainbows email id.
Finally there are the functions that allow you to perform actions on the switches.
"""



#for arg in sys.argv:
script_name = sys.argv[0]

os.system('logger -t montag -p user.info Executing script ' + script_name)

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

#switch credentials
#user = "admin"
#password = "switch"
#host = "192.168.80.27"


def format_mac(mac):
    mac = re.sub('[.:-]', '', mac).lower()  # remove delimiters and convert to lower case
    mac = ''.join(mac.split())  # remove whitespaces
    assert len(mac) == 12  # length should be now exactly 12 (eg. 008041aefd7e)
    assert mac.isalnum()  # should only contain letters and numbers
    # convert mac in canonical form (eg. 00:80:41:ae:fd:7e)
    mac = ":".join(["%s" % (mac[i:i+2]) for i in range(0, 12, 2)])
    return mac



def enable_debugging(user,password,ipadd):
    """ 
    This function enables the debugging on the switch put in arguments.

    :param str user:                Switch user login
    :param str password:            Switch user password
    :param str ipadd:               Switch IP Address
    :return:                        None
    """

    cmd = "swlog appid bcmd subapp 3 level debug2"
    #ssh session to start python script remotely
    os.system('logger -t montag -p user.info swlog activation')
    os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(password, user, ipadd, cmd))





def disable_debugging(user,password,ipadd):
    """ 
    This function disables the debugging on the switch put in arguments.

    :param str user:                Switch user login
    :param str password:            Switch user password
    :param str ipadd:               Switch IP Address
    :return:                        None
    """


    cmd = "swlog appid bcmd subapp all level info"
    #ssh session to start python script remotely
    os.system('logger -t montag -p user.info swlog desactivation')
    os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(password, user, ipadd, cmd))
#    info = "We have disable debug logs on OmniSwitch {0}".format( ipadd)



def enable_debugging_ddos(user,password,ipadd):
    """ 
    This function enables the debugging level 3 on the switch put in arguments,to get more details in log.

    :param str user:                Switch user login
    :param str password:            Switch user password
    :param str ipadd:               Switch IP Address
    :return:                        None
    """

    cmd = "swlog appid ipv4 subapp all level debug3"
    #ssh session to start python script remotely
    os.system('logger -t montag -p user.info debug3 for ddos  activation')
    os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(password, user, ipadd, cmd))



def disable_debugging_ddos(user,password,ipadd):
    """ 
    This function disables the debugging level 3 on the switch put in arguments,to get more details in log.

    :param str user:                Switch user login
    :param str password:            Switch user password
    :param str ipadd:               Switch IP Address
    :return:                        None
    """

    cmd = "swlog appid ipv4 subapp all level info"
    #ssh session to start python script remotely
    os.system('logger -t montag -p user.info debug3 for ddos  activation')
    os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(password, user, ipadd, cmd))


def disable_port(user,password,ipadd,portnumber):
    """ 
    This function disables the port where there is a loop  on the switch put in arguments.

    :param str user:                Switch user login
    :param str password:            Switch user password
    :param str ipadd:               Switch IP Address
    :param str portnumber:          The Switch port where there is a loop. shape : x/y/z with x = chassis n° ; y = slot n° ; z = port n°
    :return:                        None
    """
    cmd = "interfaces port {0} admin-state disable".format(portnumber)
    #ssh session to start python script remotely
    os.system('logger -t montag -p port disabling')
    os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(password, user, ipadd, cmd))
    os.system('logger -t montag -p user.info Following port is administratively disabled: ' + portnumber)

def enable_port(user,password,ipadd,portnumber):
    """ 
    This function enables the port where there is a loop  on the switch put in arguments.

    :param str user:                Switch user login
    :param str password:            Switch user password
    :param str ipadd:               Switch IP Address
    :param str portnumber:          The Switch port where there is a loop. shape : x/y/z with x = chassis n° ; y = slot n° ; z = port n°
    :return:                        None
    """
    cmd = "interfaces port {0} admin-state enable".format(portnumber)
    #ssh session to start python script remotely
    os.system('logger -t montag -p port enabling')
    os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(password, user, ipadd, cmd))
    os.system('logger -t montag -p user.info Following port is administratively enabled: ' + portnumber)

def enable_qos_ddos(user,password,ipadd,ipadd_ddos):
  file_setup_qos(ipadd_ddos)
  with pysftp.Connection(host=ipadd, username=user, password=password) as sftp:
    with sftp.cd('working'):             # temporarily chdir to public
        sftp.put('/opt/ALE_Script/configqos')  # upload file to public/ on remote
        sftp.get('configqos')         # get a remote file

  cmd = "configuration apply ./working/configqos "
  os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(password, user, ipadd,cmd))


def disable_qos_ddos(user,password,ipadd,ipadd_ddos):
  file_unset_qos(ipadd_ddos)
  with pysftp.Connection(host=ipadd, username=user, password=password) as sftp:
    with sftp.cd('working'):             # temporarily chdir to public
        sftp.put('/opt/ALE_Script/configqos')  # upload file to public/ on remote
        sftp.get('configqos')         # get a remote file

  cmd = "configuration apply ./working/configqos "
  os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(password, user, ipadd,cmd))


def file_setup_qos(addr):
    content_variable = open ('/opt/ALE_Script/configqos','w')
    if re.search(r"\:", addr): #mac
        setup_config= "policy condition scanner_{0} source mac {0}\npolicy action block_mac disposition deny\npolicy rule scanner_{0} condition scanner_{0} action block_mac\nqos apply".format(addr)
    else:	
    	setup_config= "policy condition scanner_{0} source ip {0}\npolicy action block_ip disposition deny\npolicy rule scanner_{0} condition scanner_{0} action block_ip\nqos apply".format(addr)
    content_variable.write(setup_config)
    content_variable.close()


def file_unset_qos(ipadd):
    content_variable = open ('/opt/ALE_Script/configqos','w')
    setup_config= "no policy rule rule_{0}\nno policy condition scanner_{0}\nqos apply".format(ipadd)
    content_variable.write(setup_config)
    content_variable.close()


def send_python_file_sftp(user,password,ipadd,filename):
  with pysftp.Connection(host=ipadd, username=user, password=password) as sftp:
    with sftp.cd('/flash/python'):             # temporarily chdir to public
        sftp.put('/opt/ALE_Script/{0}'.format(filename))  # upload file to public/ on remote
        sftp.get(filename)         # get a remote file

def get_file_sftp(user,password,ipadd,filename):
   date = datetime.date.today()
   date_hm = datetime.datetime.today()

   with pysftp.Connection(host=ipadd, username=user, password=password) as sftp:
      sftp.get('./{0}'.format(filename), '/tftpboot/{0}_{1}-{2}_{3}_{4}'.format(date,date_hm.hour,date_hm.minute,ipadd,filename))         # get a remote file

def detect_port_loop():
        """ 
        This function detectes if there is a loop in the network ( more than 10 log in 2 seconds)

        :param:                         None
        :return int :                  If the int is equal to 1 we have detected a loop, if not the int equals 0
        """

        content_variable = open ('/var/log/devices/lastlog_loop.json','r')
        file_lines = content_variable.readlines()
        content_variable.close()
        if len(file_lines) > 150:
           #clear lastlog file
           open('/var/log/devices/lastlog_loop.json','w').close()

        if len(file_lines) >= 10:
           #check if the time of the last and the tenth last are less than seconds


           #first _ line
           first_line = file_lines[0].split(',')
           first_time = first_line[0]

           #last_line
           last_line = file_lines[9].split(',')
           last_time = last_line[0] 

           #extract the timestamp (first_time and last_time)
           first_time_split = first_time[-len(first_time)+26:-7].split(':')
           last_time_split = last_time[-len(last_time)+26:-7].split(':')

           #time in hour into decimal of the first time : #else there is en error due to second  changes 60 to 0
           hour = first_time_split[0]
           #"%02d" %  force writing on 2 digits
           minute_deci = "%02d" % int(float(first_time_split[1])*100/60)
           second_deci = "%02d" % int(float(first_time_split[2])*100/60)
           first_time = "{0}{1}{2}".format(hour,minute_deci,second_deci)

           #time in hour into decimal of the last time : #else there is en error due to second  changes 60 to 0
           hour = last_time_split[0]
           #"%02d" %  force writing on 2 digits
           minute_deci = "%02d" % int(float(last_time_split[1])*100/60)
           second_deci = "%02d" % int(float(last_time_split[2])*100/60)
           last_time = "{0}{1}{2}".format(hour,minute_deci,second_deci)




           if(int(last_time)-int(first_time)) < 1: #diff less than 2 seconds ( we can down to 1)
              return 1
           else:
              #clear lastlog file
              open('/var/log/devices/lastlog_loop.json','w').close()
              return 0
        else:
           return 0






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
                        open('/var/log/devices/lastlog_flapping.json','w').close()


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
                 write_api.write(bucket, org, [{"measurement": "support_switch_port_flapping.py", "tags": {"IP_Address": ipadd, "Port": portnumber}, "fields": {"count": 1}}])
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
        open('/var/log/devices/lastlog_flapping.json','w').close()
        return "0","0","1/1/0","1/1/0"

def save_attachment(ipadd):
  myDate = datetime.date.today()
  path_log_attachment = "/var/log/devices/{0}_{1}_history.json".format(ipadd,myDate.isoformat())


  content_variable = open (path_log_attachment,'r')
  file_lines = content_variable.readlines()
  content_variable.close()
  if len(file_lines)>100:
    attachment = file_lines[-100:]
  else:
    attachment = file_lines[-len(file_lines)-1:]
  f_attachment = open('/var/log/devices/attachment.log','w')
  f_attachment.write("\n".join(attachment))
  f_attachment.close()


def save_attachment_deauth(ipadd,device_mac,timestamp):

  path_log_attachment = "/var/log/devices/{0}/syslog.log".format(ipadd)

  content_variable = open (path_log_attachment,'r')
  file_lines = content_variable.readlines()
  content_variable.close()
           #check if the time of the last and the tenth last are less than seconds

  logs_saved = list()

  #last_line
  last_line = file_lines[-1].split(',')
  last_time = last_line[0]
  last_time_split = last_time[-len(last_time)+26:-7].split(':')
  #time in hour into decimal of the last time : #else there is en error due to second  changes 60 to 0
  hour = last_time_split[0]
  #"%02d" %  force writing on 2 digits
  minute_deci = "%02d" % int(float(last_time_split[1])*100/60)
  second_deci = "%02d" % int(float(last_time_split[2])*100/60)
  last_time = "{0}{1}{2}".format(hour,minute_deci,second_deci)

  #We start from the last line
  for line in reversed(file_lines):

       current_line = line.split(',')
       current_time = current_line[0]
       #time in hour into decimal of the last time : #else there is en error due to second  changes 60 to 0
       current_time_split = current_time[-len(current_time)+26:-7].split(':')
       hour = current_time_split[0]
       #"%02d" %  force writing on 2 digits
       minute_deci = "%02d" % int(float(current_time_split[1])*100/60)
       second_deci = "%02d" % int(float(current_time_split[2])*100/60)
       current_time = "{0}{1}{2}".format(hour,minute_deci,second_deci)

       if (int(last_time)-int(current_time)) > timestamp:
          break

       for element in current_line:
          if re.search(device_mac,element):
             logs_saved.append(line)


  attachment = reversed(logs_saved)
  f_attachment = open('/var/log/devices/attachement.log','w')
  f_attachment.write("".join(attachment))
  f_attachment.close()


def collect_log_usb(user,password,ipadd):
     """ 
     This function sends the command to collect log on a usb key of the switch put in arguements.

     :param str user:                Switch user login
     :param str password:            Switch user password
     :param str ipadd:               Switch IP Address
     :param str portnumber:          The Switch port where there is a loop. shape : x/y/z with x = chassis n° ; y = slot n° ; z = port n°
     :return:                        None
     """

     #ssh session to start python script remotely
     cmd = "python3 /flash/python/get_logs_usb_key.py"
     logging.info(runtime + ': upload starting')
     os.system("sshpass -p 'Letacla01*' ssh -v {0}@{1} {2}".format(user, ip_host, cmd))
     logging.info(runtime + ' Process finished!')




def extract_ip_port(log):
        """ 
        This function collects the IP address of the switch, in the log.
        if, this is a loop log , the function collect also the port number, otherwise the port is set as 0.

        :param string log:              Can take loop or flapping
        :return str ipadd:              Switch IP Address in the log file
        :return str portnumber:         The Switch port where there is a loop. shape : x/y/z with x = chassis n° ; y = slot n° ; z = port n°
        """

        #open the file lastlog  and take the first line of the file
        
        if log == "qos_ddos":
            content_variable = open ('/var/log/devices/lastlog_ddos_ip.json','r')
        if log == "debug_ddos":
           content_variable = open ('/var/log/devices/lastlog_ddos.json','r')
        if log == "loop":
           content_variable = open ('/var/log/devices/lastlog_loop.json','r') 
        if log == "debug":
           content_variable = open ('/var/log/devices/lastlog.json','r')
        if log == "get_log_ap":
           content_variable = open ('/var/log/devices/get_log_ap.json','r')
        if log == "get_log_switch":
           content_variable = open ('/var/log/devices/get_log_switch.json','r')
        if log =="deauth_ap":
           content_variable = open ('/var/log/devices/lastlog_deauth.json','r')
        if log == "power_supply_down":
           content_variable = open ('/var/log/devices/lastlog_power_supply_down.json','r')
        if log == "vc_down":
           content_variable = open ('/var/log/devices/lastlog_vc_down.json','r')

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
            Prtnum= 0
          #For each element, look if port is present. If yes,  we take the next element which is the port number
          if "port" in element:
            element_split = element.split()
            for i in range(len(element_split)):
             if element_split[i]=="port":
              x = element_split[i+1]
            #looking for chassis ID number:
              Prtnum = "1/1/{}".format(x)   #modify the format of the port number to suit the switch interface
          if "LINKSTS" in element:
             element_split = element.split()
             for i in range(len(element_split)):
                 if element_split[i]=="port":
                    x = element_split[i+1]
                    #looking for chassis ID number:
                    Prtnum = x.replace('\\','')   #modify the format of the port number to suit the switch interface

          if "reason" in element:
            element_split = element.split()
            for i in range(len(element_split)):
               if element_split[i]=="reason":
                  reason_violation = 0
                  reason_violation_a = element_split[i+1]
                  reason_violation_b = element_split[i+2]
                  reason_violation = reason_violation_a  + reason_violation_b
                  reason_violation = reason_violation.strip(" \"[]")
                  print(reason_violation)
                  os.system('logger -t montag -p user.info Violation on port reason: ' + reason_violation)
               else:
                  pattern_AP_MAC = re.compile('.*\((([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\).*')
                  pattern_Device_MAC = re.compile('.*\[(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\].*')
#                 device_mac = re.search(pattern_Device_MAC, str(f)).group(1)
#                 ap_mac = re.search(pattern_AP_MAC, str(f)).group(1)

          if "Supply" in element:
             element_split = element.split()
             for i in range(len(element_split)):
                 if element_split[i]=="Supply":
                    nb_power_supply = element_split[i+1]
          if "chassis" in element:
             element_split = element.split()
             for i in range(len(element_split)):
                 if element_split[i]=="chassis":
                    nb_vc = element_split[i+1]

        else:
          print("Lastlog file is empty")
          os.system('logger -t montag -p user.info Lastlog file is empty')
          ipadd = "0"
          Prtnum = "0"
        if log =="deauth_ap":
           return ipadd,device_mac,ap_mac
        if log == "power_supply_down":
           return ipadd, nb_power_supply
        if log == "vc_down":
           return ipadd, nb_vc
        else:
           return ipadd,Prtnum






def extract_ip_ov():
  """ 
  This function extracts the ip adresse of all devices in the device catalog.

  :param :                        None
  :return:                        None
  """
  new_file = ""
  content_variable = open ('/opt/ALE_Script/Devices.csv','r')
  file_lines = content_variable.readlines()
  content_variable.close()
  file_lines = file_lines[2:len(file_lines)-1]
  print(file_lines)
  for element in file_lines:
     element_split = element.split(';')
     new_file = new_file +  element_split[1] + ","


  f_attachment = open('/opt/ALE_Script/device_catalog.conf','w')
  f_attachment.write(new_file)
  f_attachment.close()

def extract_ip_ap():
  """
  This function extracts the ip adresse of all devices in the device catalog.

  :param :                        None
  :return:                        None
  """
  new_file = ""
  content_variable = open ('/opt/ALE_Script/Devices_AP.csv','r')
  file_lines = content_variable.readlines()
  content_variable.close()
  file_lines = file_lines[2:len(file_lines)-1]
  print(file_lines)
  for element in file_lines:
     element_split = element.split(';')
     new_file = new_file +  element_split[1] + ","


  f_attachment = open('/opt/ALE_Script/device_AP_catalog.conf','w')
  f_attachment.write(new_file)
  f_attachment.close()


def extract_ip_ddos():
  content_variable = open ('/var/log/devices/lastlog_ddos_ip.json','r')
  file_lines = content_variable.readlines()
  if len(file_lines)!=0:
     first_line = file_lines[0]
     f=first_line.split(',')
     print(len(file_lines))
     if len(file_lines) >= 2:
         #check if the time of the last and the tenth last are less than seconds


            #first _ line
            first_line = file_lines[len(file_lines)-2].split(',')
            first_time = first_line[0]

           #last_line
            last_line = file_lines[len(file_lines)-1].split(',')
            last_time = last_line[0]

            #extract the timestamp (first_time and last_time)
            first_time_split = first_time[-len(first_time)+26:-7].split(':')
            last_time_split = last_time[-len(last_time)+26:-7].split(':')

            #time in hour into decimal of the first time : #else there is en error due to second  changes 60 to 0
            hour = first_time_split[0]
            #"%02d" %  force writing on 2 digits
            minute_deci = "%02d" % int(float(first_time_split[1])*100/60)
            second_deci = "%02d" % int(float(first_time_split[2])*100/60)
            first_time = "{0}{1}{2}".format(hour,minute_deci,second_deci)

            #time in hour into decimal of the last time : #else there is en error due to second  changes 60 to 0
            hour = last_time_split[0]
            #"%02d" %  force writing on 2 digits
            minute_deci = "%02d" % int(float(last_time_split[1])*100/60)
            second_deci = "%02d" % int(float(last_time_split[2])*100/60)
            last_time = "{0}{1}{2}".format(hour,minute_deci,second_deci)
            print(int(last_time))
            print(int(first_time))
            print(int(last_time)-int(first_time))
            if(int(last_time)-int(first_time)) >  10:
               return "0"

            for element in f:
               if "ALV4 event: PSCAN" in element:
                  sub_element = element.split(' ')
                  ip_ddos = sub_element[len(sub_element)-1][:-1]
                  print(ip_ddos)
                  return ip_ddos

     else:
           return "1"
  else:
     return "1"



def check_timestamp():
        """ 
        This function provides the time between the last log and the current log .

        :param :                        None
        :return int diff_time:          This is the time gap between the last log and the current log.
        """
        #read time of the current log processed

        content_variable = open('/var/log/devices/lastlog_loop.json','r') 
        file_lines = content_variable.readlines()
        content_variable.close()
        last_line = file_lines[0]
        f=last_line.split(',')

        timestamp_current = f[0]
        current_time = timestamp_current[-len(timestamp_current)+26:-7].replace(':' , '')

        if not os.path.exists('/var/log/devices/logtemp.json'):
          open('/var/log/devices/logtemp.json','w').close()

        #read time of the last log  processed
        f_lastlog = open('/var/log/devices/logtemp.json','r')
        first_line =  f_lastlog.readlines()

        #if logtemps is empty or more than 1 line in the file ( avoid error), clear the file
        if len(first_line)!=1 :
         f_lastlog = open('/var/log/devices/logtemp.json','w')
         f_lastlog.write(last_line)
         f_lastlog.close()

        f_lastlog_split = first_line[0].split(',')
        timestamp_last = f_lastlog_split[0]
        last_time = timestamp_last[-len(timestamp_last)+26:-7].replace(':' , '')
        diff_time = int(current_time) - int(last_time)

        return diff_time



def replace_logtemp():

        content_variable = open ('/var/log/devices/lastlog_loop.json','r')
        file_lines = content_variable.readlines()
        content_variable.close()
        last_line = file_lines[0]

           #copy log in temp
        f_lastlog = open('/var/log/devices/logtemp.json','w')
        f_lastlog.write(last_line)
        f_lastlog.close()

def get_credentials():
     """ 
     This function collects all the information about the switch's credentials in the log. 
     It collects also the information usefull for  notification sender in the file ALE_script.conf.

     :param:                         None
     :return str user:               Switch user login
     :return str password:           Switch user password
     :return str id:                 Rainbow JID  of recipients
     :return str gmail_usr:          Sender's email userID
     :return str gmail_passwd:       Sender's email password               
     :return str mails:              List of email addresses of recipients
     """

     content_variable = open ('/opt/ALE_Script/ALE_script.conf','r') #'/var/log/devices/192.168.80.27_2021-03-26.json'
     file_lines = content_variable.readlines()
     content_variable.close()
     credentials_line = file_lines[0]
     credentials_line_split = credentials_line.split(',')
     user = credentials_line_split[0]
     password = credentials_line_split[1]
     if credentials_line_split[3] != "":
        id= credentials_line_split[3]
     elif credentials_line_split[3] == "":
        id=''

     gmail_usr = credentials_line_split[4]
     gmail_passwd = credentials_line_split[5]
     mails = credentials_line_split[2].split(';')
     mails = [ element  for element  in mails]
     #mails= ", ".join(mails)
     ip_server_log = credentials_line_split[6]

     return user,password,id,gmail_usr,gmail_passwd,mails,ip_server_log


def get_credentials_ap():
     """ 
     This function collects all the information about the AP's credentials in the file ALE_script.conf.

     :param:                         None
     :return str user_ap:               AP user login
     :return str password_ap:           AP user password
     :return str technical_support_code:  Technical surpport code of APs.
     """

     content_variable = open ('/opt/ALE_Script/ALE_script.conf','r') #'/var/log/devices/192.168.80.27_2021-03-26.json'
     file_lines = content_variable.readlines()
     content_variable.close()
     credentials_line = file_lines[0]
     credentials_line_split = credentials_line.split(',')
     user_ap = credentials_line_split[7]
     password_ap = credentials_line_split[8]
     technical_support_code = credentials_line_split[9]
     return user_ap,password_ap,technical_support_code

def get_mail():
     """ 
     This function collects Mail informations in the file ALE_script.conf.

     :param:                         None
     :return str server_log_ip:  Ip Adress of log server.
     """

     content_variable = open ('/opt/ALE_Script/ALE_script.conf','r') #'/var/log/devices/192.168.80.27_2021-03-26.json'
     file_lines = content_variable.readlines()
     content_variable.close()
     credentials_line = file_lines[0]
     credentials_line_split = credentials_line.split(',')
     gmail_usr = credentials_line_split[4]
     gmail_passwd = credentials_line_split[5]
     mails = credentials_line_split[2].split(';')
     mails = [ element  for element  in mails]

     return gmail_usr,gmail_passwd,mails

def get_id_client():
     content_variable = open ('/opt/ALE_Script/ALE_script.conf','r') #'/var/log/devices/192.168.80.27_2021-03-26.json'
     file_lines = content_variable.readlines()
     content_variable.close()
     credentials_line = file_lines[0]
     credentials_line_split = credentials_line.split(',')

     id_client = credentials_line_split[10]
     return id_client

def get_server_log_ip():
     """ 
     This function collects Ip Adress of log server in the file ALE_script.conf.

     :param:                         None
     :return str server_log_ip:  Ip Adress of log server.
     """

     content_variable = open ('/opt/ALE_Script/ALE_script.conf','r') #'/var/log/devices/192.168.80.27_2021-03-26.json'
     file_lines = content_variable.readlines()
     content_variable.close()
     credentials_line = file_lines[0]
     credentials_line_split = credentials_line.split(',')
     server_log_ip = credentials_line_split[6]
     return server_log_ip

def get_jid():
     """
     This function collects Rainbow JID in the file ALE_script.conf.

     :param:                         None
     :return str jip:  Rainbow JID.
     """

     content_variable = open ('/opt/ALE_Script/ALE_script.conf','r') #'/var/log/devices/192.168.80.27_2021-03-26.json'
     file_lines = content_variable.readlines()
     content_variable.close()
     credentials_line = file_lines[0]
     credentials_line_split = credentials_line.split(',')
     jid= credentials_line_split[3]
     return jid



def add_new_save(ipadd,port,type,choice = "never"):
  """ 
  This function saves the new instruction to be recorded given by the user on Rainbow.


  :param str ipadd:              Switch IP Address
  :param str portnumber:        Switch port number
  :param str type:              What use case is it? can take : loop, flapping
  :return:                        None
  """


  if not os.path.exists('/opt/ALE_Script/decisions_save.conf'):
     open ('/opt/ALE_Script/decisions_save.conf','w').close()

  fileR = open("/opt/ALE_Script/decisions_save.conf", "r")
  text = fileR.read()
  fileR.close()

  textInsert = "{0},{1},{2},{3}\n".format(ipadd,port,type,choice)

  fileW = open("/opt/ALE_Script/decisions_save.conf", "w")
  fileW.write(textInsert + text)
  fileW.close()

def check_save(ipadd,port,type):
  if not os.path.exists('/opt/ALE_Script/decisions_save.conf'):
     open ('/opt/ALE_Script/decisions_save.conf','w').close()
     return "0"


  content = open("/opt/ALE_Script/decisions_save.conf", "r")
  file_lines = content.readlines()
  content.close()

  for line in file_lines:
    print(line)
    if  "{0},{1},{2},always".format(ipadd,port,type) in line:
       return "1"
    if "{0},{1},{2},never".format(ipadd,port,type) in line:
       return "-1"

  return '0'
