#!/usr/local/bin/python3.7
import os
import subprocess
import sys
import paramiko
from time import strftime, localtime, sleep

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

# Tue, 29 Sep 2020 20:27:24 +0000
runtime = strftime("%d_%b_%Y_%H_%M_%S_0000", localtime())

switch_user = "admin"
switch_password = "switch"

port = ipadd = ""
if len(sys.argv) > 1:
    ipadd = sys.argv[1]
    port = sys.argv[2]

    print(bcolors.WARNING + "We received following ip address and port as arguments " + ipadd + " / " + port + bcolors.ENDC)

else:
    print(bcolors.FAIL + "No arguments received" + bcolors.ENDC)
    exit()

system_name = os.uname()[1].replace(" ", "_")

print(bcolors.WARNING + "Starting Port Flapping" + bcolors.ENDC)

l_switch_cmd = []
l_switch_cmd.append("echo \"date\" | su")
l_switch_cmd.append("interfaces port " + port + " admin-state disable")
sleep(0.2)
l_switch_cmd.append("interfaces port " + port + " admin-state enable")
sleep(0.2)
l_switch_cmd.append("interfaces port " + port + " admin-state disable")
sleep(0.2)
l_switch_cmd.append("interfaces port " + port + " admin-state enable")
sleep(0.2)
l_switch_cmd.append("interfaces port " + port + " admin-state disable")
sleep(0.2)
l_switch_cmd.append("interfaces port " + port + " admin-state enable")
sleep(0.2)
l_switch_cmd.append("interfaces port " + port + " admin-state disable")
sleep(0.2)
l_switch_cmd.append("interfaces port " + port + " admin-state enable")
sleep(0.2)
l_switch_cmd.append("interfaces port " + port + " admin-state disable")
sleep(0.2)
l_switch_cmd.append("interfaces port " + port + " admin-state enable")
sleep(0.2)
l_switch_cmd.append("interfaces port " + port + " admin-state disable")
sleep(0.2)
l_switch_cmd.append("interfaces port " + port + " admin-state enable")
sleep(0.2)
l_switch_cmd.append("interfaces port " + port + " admin-state disable")
sleep(0.2)
l_switch_cmd.append("interfaces port " + port + " admin-state enable")
sleep(0.2)
l_switch_cmd.append("interfaces port " + port + " admin-state disable")
sleep(0.2)
l_switch_cmd.append("interfaces port " + port + " admin-state enable")
sleep(0.2)
l_switch_cmd.append("interfaces port " + port + " admin-state disable")
sleep(0.2)
l_switch_cmd.append("interfaces port " + port + " admin-state enable")
sleep(0.2)
l_switch_cmd.append("interfaces port " + port + " admin-state disable")
sleep(0.2)
l_switch_cmd.append("interfaces port " + port + " admin-state enable")
sleep(0.2)

for switch_cmd in l_switch_cmd:
    cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user, ipadd, switch_cmd)
    try:
        output = subprocess.call(cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
        if output == 0:
            print(switch_cmd + " - Command executed with success")
    except subprocess.SubprocessError:
        print("Issue when executing command")

print(bcolors.WARNING + "End of Port Flapping" + bcolors.ENDC)
