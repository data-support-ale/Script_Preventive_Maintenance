#!/usr/bin/env python

import logging
from time import gmtime, strftime, localtime
import os
import subprocess
import sys
import getpass
import time
import getopt
import datetime
from time import gmtime, strftime, localtime, sleep


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


logging.basicConfig(
    filename="/flash/python/get_logs_usb.log", level=logging.DEBUG)

# Tue, 29 Sep 2020 20:27:24 +0000
runtime = strftime("%d_%b_%Y_%H_%M_%S_0000", localtime())

system_name = os.uname()[1].replace(" ", "_")

logging.info("### OmniSwitch starting get logs on {0} at {1} ###".format(
    system_name, runtime))
print(bcolors.WARNING + "Collecting log script starting" + bcolors.ENDC)

port = ""
if len(sys.argv) > 1:
    port = sys.argv[1]
    print(port)
    logging.info(port)

print(bcolors.WARNING + "Collecting interface command output" + bcolors.ENDC)
#interface_check = subprocess.run(["show", "interfaces", "port", port], capture_output=True)
# logging.info(interface_check)

print(bcolors.WARNING + "Collecting port flapping su command outputs" + bcolors.ENDC)

#command="echo \"md 0xFF010008\" | su"
#output=subprocess.check_output(command, stderr=subprocess.DEVNULL, timeout=40, shell=True)
# print(output)
##########################Get More LOGS########################################
text = "More logs about the switch : {0} \n\n\n".format(system_name)

l_switch_cmd = []
l_switch_cmd.append("show virtual-chassis topology")
l_switch_cmd.append("show chassis")

l_switch_cmd.append("echo \"top\" | su")
l_switch_cmd.append("echo \"free -m\" | su")
l_switch_cmd.append("echo \"cat \/proc\/meminfo\" | su")
#l_switch_cmd.append("show chassis")


for switch_cmd in l_switch_cmd:
    cmd = switch_cmd
    run = cmd.split()
    output = subprocess.check_output(
        switch_cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
    #p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE, executable='/bin/bash')
    #out, err = p.communicate()
    output = output.decode('UTF-8').strip()

    text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output)

date = datetime.date.today()
date_hm = datetime.datetime.today()

filename = "{0}_logs".format(system_name)
f_logs = open('/flash/python/{0}.txt'.format(filename), 'w')
f_logs.write(text)
f_logs.close()

logging.info("Logs collected")
