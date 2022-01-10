#!/usr/bin/env python

import prometheus_client
import sys
import os
import csv
from support_tools import get_credentials
from time import strftime, localtime, sleep
import subprocess
import re
from collections import Counter

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
SYSTEM_MEM = prometheus_client.Gauge("MEM", 'Metrics scraped with python', ['name', 'ip', 'chassis', 'slot'])
SYSTEM_CPU = prometheus_client.Gauge("CPU", 'Metrics scraped with python', ['name', 'ip', 'chassis', 'slot'])
SYSTEM_TEMP = prometheus_client.Gauge("TEMP", 'Metrics scraped with python', ['name', 'ip', 'chassis'])
SYSTEM_ARP = prometheus_client.Gauge("ARP_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_MAC_BRIDGING = prometheus_client.Gauge("MAC_Learning_Bridging_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_MAC_SERVICING = prometheus_client.Gauge("MAC_Learning_Servicing_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_MAC_FILTERING = prometheus_client.Gauge("MAC_Learning_Filtering_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_UNP_USER_ACTIVE = prometheus_client.Gauge("UNP_User_Active_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_UNP_USER_BLOCK = prometheus_client.Gauge("UNP_User_Block_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_ROUTING_LOCAL = prometheus_client.Gauge("Routing_Table_Local_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_ROUTING_STATIC = prometheus_client.Gauge("Routing_Table_Static_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_ROUTING_OSPF = prometheus_client.Gauge("Routing_Table_Ospf_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_ROUTING_IBGP = prometheus_client.Gauge("Routing_Table_Ibgp_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_ROUTING_EBGP = prometheus_client.Gauge("Routing_Table_Ebgp_Entries", 'Metrics scraped with python', ['name', 'ip'])
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
            print(ipadd + ' IP Address')
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
            try: 
                SYSTEM_MEM.labels(name=name, ip=ipadd, chassis=chassis, slot=slot).set(mem)
            except ValueError:
                pass

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
            try:
                SYSTEM_CPU.labels(name=name, ip=ipadd, chassis=chassis, slot=slot).set(cpu)
            except ValueError:
                pass

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
            try:            
                SYSTEM_TEMP.labels(name=name, ip=ipadd, chassis=chassis).set(temp)
            except ValueError:
                pass

        # ARP Entries
        switch_cmd = "show arp"
        try:
            cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user,
                                                                                       ipadd,
                                                                                       switch_cmd)
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, shell=True)
            output = output.decode('UTF-8').strip()
        except subprocess.CalledProcessError:
            continue
        matchs_arp_entries = re.findall(r"Total (\d*) arp entries", output)
        
        for arp_entries in matchs_arp_entries:
            SYSTEM_ARP.labels(name=name, ip=ipadd).set(arp_entries)

        # MAC-Learning Entries
        switch_cmd = "show mac-learning"
        try:
            cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user,
                                                                                       ipadd,
                                                                                       switch_cmd)
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, shell=True)
            output = output.decode('UTF-8').strip()
        except subprocess.CalledProcessError:
            continue
        matchs_mac_learning_bridging_entries = 0
        matchs_mac_learning_servicing_entries = 0
        matchs_mac_learning_filtering_entries = 0
        count = dict(Counter(output.split()))
        try:
            matchs_mac_learning_bridging_entries = count['bridging']
            SYSTEM_MAC_BRIDGING.labels(name=name, ip=ipadd).set(matchs_mac_learning_bridging_entries)
        except KeyError:
            pass
        print(matchs_mac_learning_bridging_entries)
        try:
            matchs_mac_learning_servicing_entries = count['servicing']
            SYSTEM_MAC_SERVICING.labels(name=name, ip=ipadd).set(matchs_mac_learning_servicing_entries)
        except KeyError:
            pass
        print(matchs_mac_learning_servicing_entries)
        try:
            print("je suis ici")
            matchs_mac_learning_filtering_entries = count['filtering']
            SYSTEM_MAC_FILTERING.labels(name=name, ip=ipadd).set(matchs_mac_learning_filtering_entries)
        except KeyError:
            pass
        print(matchs_mac_learning_filtering_entries)
        
                # UNP User metrics
        switch_cmd = "show unp user"
        try:
            cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user,
                                                                                       ipadd,
                                                                                       switch_cmd)
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, shell=True)
            output = output.decode('UTF-8').strip()
        except subprocess.CalledProcessError:
            continue
        matchs_unp_user_active_entries = 0
        matchs_unp_user_block_entries = 0
        count = dict(Counter(output.split()))
        print(ipadd + 'UNP User Table')
        try:
            matchs_unp_user_active_entries = count['Active']
            print(matchs_unp_user_active_entries)
            SYSTEM_UNP_USER_ACTIVE.labels(name=name, ip=ipadd).set(matchs_unp_user_active_entries)
        except KeyError:
            pass

        try:
            matchs_unp_user_block_entries = count['Block']
            print(matchs_unp_user_block_entries)
            SYSTEM_UNP_USER_BLOCK.labels(name=name, ip=ipadd).set(matchs_unp_user_block_entries)
        except KeyError:
            pass

                # Routing Table metrics
        switch_cmd = "show ip routes"
        try:
            cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user,
                                                                                       ipadd,
                                                                                       switch_cmd)
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, shell=True)
            output = output.decode('UTF-8').strip()
        except subprocess.CalledProcessError:
            continue
        matchs_routing_table_local_entries = 0
        matchs_routing_table_static_entries = 0
        matchs_routing_table_ospf_entries = 0
        matchs_routing_table_ibgp_entries = 0
        matchs_routing_table_ebgp_entries = 0
        count = dict(Counter(output.split()))
        print(ipadd + 'Routing Table')
        try:
            matchs_routing_table_local_entries = count['LOCAL']
            print(matchs_routing_table_local_entries)
            SYSTEM_ROUTING_LOCAL.labels(name=name, ip=ipadd).set(matchs_routing_table_local_entries)
        except KeyError:
            pass

        try:
            matchs_routing_table_static_entries = count['STATIC']
            print(matchs_routing_table_static_entries)
            SYSTEM_ROUTING_STATIC.labels(name=name, ip=ipadd).set(matchs_routing_table_static_entries)
        except KeyError:
            pass

        try:
            matchs_routing_table_ospf_entries = count['OSPF']
            SYSTEM_ROUTING_OSPF.labels(name=name, ip=ipadd).set(matchs_routing_table_ospf_entries)
        except KeyError:
            pass

        try:
            matchs_routing_table_ibgp_entries = count['IBGP']
            SYSTEM_ROUTING_IBGP.labels(name=name, ip=ipadd).set(matchs_routing_table_ibgp_entries)
        except KeyError:
            pass

        try:
            matchs_routing_table_ebgp_entries = count['EBGP']
            SYSTEM_ROUTING_EBGP.labels(name=name, ip=ipadd).set(matchs_routing_table_ebgp_entries)
        except KeyError:
            pass

    sleep(300)
