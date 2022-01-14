#!/usr/bin/env python

import sys
import os
import getopt
import json
import logging
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

logging.basicConfig(filename='/home/pi/debug_AP.log', filemode='w', level=logging.DEBUG)

runtime = strftime("%d_%b_%Y_%H_%M_%S_0000", localtime())
uname = os.system('uname -a')
system_name = os.uname()[1].replace(" ", "_")
logging.info("Running on {0} at {1} ".format(system_name, runtime))

user = "root"
host = "192.168.0.8"
cmd = "/usr/sbin/take_snapshot.sh start 192.168.0.54"

logging.info(bcolors.OKGREEN + runtime + ': upload starting' + bcolors.ENDC)
# Package sshpass must be installed 'sudo apt-get install sshpass'
os.system("sshpass -p '87e8889341936e787f704980b05063d1fa6954bc37eed6d7c46afbfee8bbda98' ssh -v -o StrictHostKeyChecking=no {0}@{1} {2}".format(user, host, cmd))
logging.info(bcolors.OKGREEN + 'Process finished!' + bcolors.ENDC)

