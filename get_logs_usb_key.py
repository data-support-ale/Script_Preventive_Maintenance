#!/usr/bin/env python3

# Script to be executed on demand or on event-action to collect and store show tech-support eng complete logs and PMD directory

# Written by Benjamin Eggerstedt and Steffen Monnier, adapted for TS Team

# Release History
# v1: 02.11.2020 - check USB key available, apply show tech-support eng complete and store logs on USB key

import logging
from time import gmtime, strftime, localtime
from distutils.dir_util import mkpath
import os
import subprocess
import sys
import getpass
# library for shutil.copy file
import shutil
import time
import getopt

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

	
logging.basicConfig(filename="/flash/python/get_logs_usb.log", level=logging.DEBUG)

#Tue, 29 Sep 2020 20:27:24 +0000
runtime = strftime("%d_%b_%Y_%H_%M_%S_0000", localtime())

system_name = os.uname()[1].replace(" ", "_")

logging.info("### OmniSwitch starting get logs on {0} at {1} ###".format(system_name, runtime))
print(bcolors.WARNING + "Collecting log script starting" + bcolors.ENDC)

print(bcolors.WARNING + "Prerequisite: USB STICK SHOULD BE INSERTED, PROPERLY FORMATTED AND HAVE ENOUGH FREE SPACE!" + bcolors.ENDC)

# Address scenarios in which we run in "aaa switch-access mode enhanced"
aaa_enhanced = None

print(bcolors.WARNING + "Checking if this OmniSwitch operates in \"aaa switch-access mode enhanced\"" + bcolors.ENDC)
aaa_check = subprocess.run(["show", "aaa", "switch-access", "mode"], capture_output=True)
if "Enhanced" in aaa_check.stdout.decode("utf-8"):
    print(bcolors.OKGREEN + "Detected \"aaa switch-access mode\": Enhanced" + bcolors.ENDC)
    logging.info("Detected \"aaa switch-access mode\": Enhanced")
    aaa_enhanced = 1
    admin_pw = getpass.getpass("Please enter the config-mode-user ({0}) password: ".format(os.environ["USER"]))
else:
    print(bcolors.OKGREEN + "Detected \"aaa switch-access mode\": Default" + bcolors.ENDC)
    logging.info("Detected \"aaa switch-access mode\": Default")

# capture_output will write the output into usb_enabled variable instead of console
usb_enabled = subprocess.run(["show", "usb", "statistics"], capture_output=True)

print(bcolors.WARNING + "Checking if USB is enabled and if USB stick is present/mounted" + bcolors.ENDC)
if "usb: enable" in usb_enabled.stdout.decode("utf-8"):
    if "usb mount mode: sync" not in usb_enabled.stdout.decode("utf-8"):
        sys.exit("Tried to enable USB, but Flash Disk not mounted! Check output of \"show usb statistics\"")
    print(bcolors.OKGREEN + "USB is enabled & mounted properly" + bcolors.ENDC)
elif "usb: disable" in usb_enabled.stdout.decode("utf-8"):
    print(bcolors.FAIL + "USB is disabled!" + bcolors.ENDC)
    print(bcolors.WARNING + "Enabling USB!" + bcolors.ENDC)
    enable_usb = subprocess.run(["usb", "enable"], capture_output=True)
    print(bcolors.WARNING + "Checking if USB stick was properly mounted!" + bcolors.ENDC)
    usb_enabled = subprocess.run(["show", "usb", "statistics"], capture_output=True)
    if "usb mount mode: sync" not in usb_enabled.stdout.decode("utf-8"):
        sys.exit(bcolors.FAIL + "Tried to enable USB, but Flash Disk not mounted! Check output of \"show usb statistics\"" + bcolors.ENDC)
else:
    pass

print(bcolors.WARNING + "Running on {0} look for \"{0}_{1}\" on USB stick".format(system_name, runtime) + bcolors.ENDC)

# Check and display how much free space is left on OmniSwitch
os_diskfree_before = subprocess.run(["freespace"], capture_output=True)
os_diskfree_before = os_diskfree_before.stdout.decode("utf-8").split()[3]
print(bcolors.WARNING + "{0} Bytes ({1:.2f} MB) free on {2}".format(os_diskfree_before, (int(os_diskfree_before) / 1024 / 1024), system_name) + bcolors.ENDC)
logging.info("{0} Bytes ({1:.2f} MB) free on {2}".format(os_diskfree_before, (int(os_diskfree_before) / 1024 / 1024), system_name))


# Address AOS 8.6R1 bug: "showFreespace.c: statvfs error(/uflash)" output
# Fixed in later AOS releases
# Figure out how much free space is left on USB stick -> Warn if less than 450 MB free
usb_diskfree_before = subprocess.run(["freespace", "/uflash"], capture_output=True)
if "showFreespace.c" in usb_diskfree_before.stdout.decode("utf-8"):
    print(bcolors.FAIL + "Output gave a bogus result, can't find freespace for USB disk - probably a bug in AOS!" + bcolors.ENDC)
    logging.info("Output gave a bogus result, can't find freespace for USB disk - probably a bug in AOS!")
else:
    usb_diskfree_before = usb_diskfree_before.stdout.decode("utf-8").split()[1]
    print(bcolors.WARNING + "{0} Bytes ({1:.2f} MB) free on USB stick".format(usb_diskfree_before, (int(usb_diskfree_before) / 1024 / 1024)) + bcolors.ENDC)
    logging.info("{0} Bytes ({1:.2f} MB) free on USB stick".format(usb_diskfree_before, (int(usb_diskfree_before) / 1024 / 1024)))
    if (int(usb_diskfree_before) / 1024 / 1024) < 450:
        print(bcolors.FAIL + "Less than 450 MB free on the USB stick, this script will fail soon. Clean up your USB stick!" + bcolors.ENDC)
        logging.info("Less than 450 MB free on the USB stick, this script will fail soon. Clean up your USB stick!")

print(bcolors.WARNING + "Creating directory: /uflash/{0}_{1}".format(system_name, runtime) + bcolors.ENDC)
logging.info("Creating directory: /uflash/{0}_{1}".format(system_name, runtime))
mkpath("/uflash/{0}_{1}".format(system_name, runtime))

if os.path.exists("/flash/tech_support_complete.tar"):
    print(bcolors.WARNING + "If previous Tech Support exists, removing tar file" + bcolors.ENDC)
    logging.info("If previous Tech Support exists, removing tar file")
    os.remove("/flash/tech_support_complete.tar")

# Collect logs with command show tech-support eng complete
subprocess.run(["show", "tech-support", "eng", "complete"])

n = 100  # or however many loading slots you want to have
load = 0.5  # artificial loading time!
loading = '.' * n  # for strings, * is the repeat operator


# while loop until above command is complete

while(os.path.exists("/flash/tech_support_complete.tar")==False):
    print(bcolors.WARNING + "Tech Support Complete in progress" + bcolors.ENDC)
    for i in range(n+1):
        # this loop replaces each dot with a hash!
        print(bcolors.WARNING + '\r%s Loading %3d percent!' % (loading, i*100/n), end='' + bcolors.ENDC)
        loading = loading[:i] + '#' + loading[i+1:]
        time.sleep(load)
    if os.path.exists("/flash/tech_support_complete.tar"):
        break
print("\b")
print(bcolors.WARNING + "Tech Support Complete done, storing file into USB key, path /uflash/{0}_{1}/tech_support_complete.tar".format(system_name, runtime) + bcolors.ENDC)
subprocess.run(["/bin/cp", "/flash/tech_support_complete.tar", "/uflash/{0}_{1}/".format(system_name, runtime)])

