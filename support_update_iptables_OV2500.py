#!/usr/bin/env python3

import sys
import os
import getopt
import json
import logging
import subprocess
import re
from time import gmtime, strftime, localtime

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

#logging.basicConfig(filename='/home/pi/debug_AP.log', filemode='w', level=logging.DEBUG)

runtime = strftime("%d_%b_%Y_%H_%M_%S_0000", localtime())
uname = os.system('uname -a')
system_name = os.uname()[1].replace(" ", "_")
logging.info("Running on {0} at {1} ".format(system_name, runtime))


if len(sys.argv) == 2 :
   if not re.search("^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", sys.argv[1]):
     print()
     print("Make sure you put an IP Address in parameter. (ex : 192.168.0.1) ")
     exit()
   host = sys.argv[1]
   user = "root"
   #host = "10.130.7.17"
   password = "223405d70e8e5c31a0f28d0517556581a0adeb7d"

   #Test if snmp trap service is start with port 1888
   cmd = "netstat -anp | grep 'udp * 0 *  0 0.0.0.0:1888'"
   run = "sshpass -p {0} ssh -p 2222 -o StrictHostKeyChecking=no {1}@{2} {3}".format(password,user,host,cmd)
   run= run.split()
   p = subprocess.Popen(run, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   out, err = p.communicate()
   result_str=out.decode('ascii').strip()

   if result_str !="":
      cmd = "iptables -L INPUT --line-numbers |grep 'udp dpt:snmp '"
      run = "sshpass -p {0} ssh -p 2222 -o StrictHostKeyChecking=no {1}@{2} {3}".format(password,user,host,cmd)
      run= run.split()
      p = subprocess.Popen(run, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      out, err = p.communicate()
      line_iptable_162=out.decode('ascii').strip()

      cmd = "iptables -L INPUT --line-numbers |grep 'custum_ovclient_trap_udp_port'"
      run = "sshpass -p {0} ssh -p 2222 -o StrictHostKeyChecking=no {1}@{2} {3}".format(password,user,host,cmd)
      run= run.split()
      p = subprocess.Popen(run, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      out, err = p.communicate()
      line_iptable_1888=out.decode('ascii').strip()


      if line_iptable_162 !=""  and line_iptable_1888=="" : #if rule 162 exists and 1888 doesn't exist
         nb_line = line_iptable_162.split()[0]
         #Delete the rule with port 162.
         cmd = "iptables -D INPUT {0}".format(nb_line)
         run = "sshpass -p {0} ssh -p 2222 -o StrictHostKeyChecking=no {1}@{2} {3}".format(password,user,host,cmd)
         run= run.split()
         p = subprocess.Popen(run, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

         #Add the rule with port 1888
         cmd = "iptables -I INPUT 20 -i eth0 -p udp -m udp --dport 1888 -m conntrack --ctstate NEW,ESTABLISHED -m comment --comment custum_ovclient_trap_udp_port -j ACCEPT_LOGGING"
         run = "sshpass -p {0} ssh -p 2222 -o StrictHostKeyChecking=no {1}@{2} {3}".format(password,user,host,cmd)
         run= run.split()
         p = subprocess.Popen(run, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
         logging.info(bcolors.OKGREEN + 'Process finished!' + bcolors.ENDC)
         print("Done. Iptable has been replaced")

         cmd = "service iptables save"
         run = "sshpass -p {0} ssh -p 2222 -o StrictHostKeyChecking=no {1}@{2} {3}".format(password,user,host,cmd)
         run= run.split()
         p = subprocess.Popen(run, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

      elif  line_iptable_162 != "" and line_iptable_1888!="" : #if rule 162 exists and rule 1888 exists
         nb_line = line_iptable_162.split()[0]
         #Delete the rule with port 162.
         cmd = "iptables -D INPUT {0}".format(nb_line)
         run = "sshpass -p {0} ssh -p 2222 -o StrictHostKeyChecking=no {1}@{2} {3}".format(password,user,host,cmd)
         run= run.split()
         p = subprocess.Popen(run, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
         print("Iptable with port 162 deleted, Iptable with port 1888 was already configured.")


      elif line_iptable_162 == "" and line_iptable_1888=="" : # if rule 162 doesn't exist and rule 1888 doesn't exist
         #Add the rule with port 1888
         cmd = "iptables -I INPUT 20 -i eth0 -p udp -m udp --dport 1888 -m conntrack --ctstate NEW,ESTABLISHED -m comment --comment custum_ovclient_trap_udp_port -j ACCEPT_LOGGING"
         run = "sshpass -p {0} ssh -p 2222 -o StrictHostKeyChecking=no {1}@{2} {3}".format(password,user,host,cmd)
         run= run.split()
         p = subprocess.Popen(run, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
         logging.info(bcolors.OKGREEN + 'Process finished!' + bcolors.ENDC)
         print("Iptable with port 1888 configured, Iptable with port 162 was already deleted.")

         cmd = "service iptables save"
         run = "sshpass -p {0} ssh -p 2222 -o StrictHostKeyChecking=no {1}@{2} {3}".format(password,user,host,cmd)
         run= run.split()
         p = subprocess.Popen(run, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


      elif line_iptable_1888!="" and line_iptable_162 == "":  ##if rule 162 doesn't exist and rule 1888 exists
         print("Iptable has already been replaced")

   else:
      print()
      print("Error : The Trap Port Number is not configured on 1888 or the service trap notification has not yet started. Retry after the port is configured or the service is started. ")
      print()
else:
   print()
   print("Make sure you put only one parameter : The OV IP Address.")
   print()
