#!/usr/bin/env python

import prometheus_client
import sys
import os
import csv
from support_tools import get_credentials
from time import strftime, localtime, sleep
import subprocess
import re

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
SYSTEM_MEM = prometheus_client.Gauge("MEM", 'Metrics scraped with python', ['name', 'ip', 'chassis', 'slot'])
SYSTEM_CPU = prometheus_client.Gauge("CPU", 'Metrics scraped with python', ['name', 'ip', 'chassis', 'slot'])
SYSTEM_TEMP = prometheus_client.Gauge("TEMP", 'Metrics scraped with python', ['name', 'ip', 'chassis'])
path = "/opt/ALE_Script/"

switch_user, switch_password, jid, gmail_user, gmail_password, mails, ip_server = get_credentials()

if __name__ == '__main__':
    prometheus_client.start_http_server(9999)

ips_address = list()
with open(path + 'Devices.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=';')
    line = 0
    for row in csv_reader:
        if line == 0:
            line = 1
            continue
        ips_address.append(str(row[1]))

while True:
    for ipadd in ips_address:
        try:
            output = subprocess.check_output(
                "ping -{} 1 {}".format('c', ipadd), shell=True)
            if not re.search(r"TTL|ttl", str(output)):
                continue
        except subprocess.CalledProcessError:
            continue

        # NAME
        switch_cmd = "show system | grep Name"
        try:
            cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user,
                                                                                       ipadd,
                                                                                       switch_cmd)
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, shell=True)
            output = output.decode('UTF-8').strip()
        except subprocess.CalledProcessError:
            continue
        name = re.findall(r"([A-Za-z0-9-]*),", output)[0]

        # MEMORY
        switch_cmd = "show health all memory"
        try:
            cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user,
                                                                                       ipadd,
                                                                                       switch_cmd)
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, shell=True)
            output = output.decode('UTF-8').strip()
        except subprocess.CalledProcessError:
            continue
        matchs_mem = re.findall(r"Slot  (\d+?)\/ (\d+?)             (\d*?) ", output)
        for chassis, slot, mem in matchs_mem:
            SYSTEM_MEM.labels(name=name, ip=ipadd, chassis=chassis, slot=slot).set(mem)

        # CPU
        switch_cmd = "show health all cpu"
        try:
            cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user,
                                                                                       ipadd,
                                                                                       switch_cmd)
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, shell=True)
            output = output.decode('UTF-8').strip()
        except subprocess.CalledProcessError:
            continue
        matchs_cpu = re.findall(r"Slot  (\d+?)\/ (\d+?)             (\d*?) ", output)
        for chassis, slot, cpu in matchs_cpu:
            SYSTEM_CPU.labels(name=name, ip=ipadd, chassis=chassis, slot=slot).set(cpu)

        # TEMP
        switch_cmd = "show temperature"
        try:
            cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user,
                                                                                       ipadd,
                                                                                       switch_cmd)
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, shell=True)
            output = output.decode('UTF-8').strip()
        except subprocess.CalledProcessError:
            continue
        matchs_temp = re.findall(r"(\d*?)/CMMA            (\d*?) ", output)
        for chassis, temp in matchs_temp:
            SYSTEM_TEMP.labels(name=name, ip=ipadd, chassis=chassis).set(temp)

    sleep(300)

