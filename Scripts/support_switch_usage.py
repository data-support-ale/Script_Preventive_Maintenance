#!/usr/local/bin/python3.7

import prometheus_client
import sys
import os
import csv
from support_tools_OmniSwitch import get_credentials
from time import strftime, localtime, sleep
import subprocess
import re
from collections import Counter
import threading
import time
import paramiko
import platform

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Prometheus metrics
SYSTEM_MEM = prometheus_client.Gauge("MEM", 'Metrics scraped with python', [
                                     'name', 'ip', 'chassis', 'slot'])
SYSTEM_CPU = prometheus_client.Gauge("CPU", 'Metrics scraped with python', [
                                     'name', 'ip', 'chassis', 'slot'])
SYSTEM_TEMP = prometheus_client.Gauge(
    "TEMP", 'Metrics scraped with python', ['name', 'ip', 'chassis'])
SYSTEM_ARP = prometheus_client.Gauge(
    "ARP_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_MAC_BRIDGING = prometheus_client.Gauge(
    "MAC_Learning_Bridging_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_MAC_SERVICING = prometheus_client.Gauge(
    "MAC_Learning_Servicing_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_MAC_FILTERING = prometheus_client.Gauge(
    "MAC_Learning_Filtering_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_MAC_FILTERING_RATIO = prometheus_client.Gauge(
    "MAC_Learning_Filtering_Ratio_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_UNP_USER_ACTIVE = prometheus_client.Gauge(
    "UNP_User_Active_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_UNP_USER_BLOCK = prometheus_client.Gauge(
    "UNP_User_Block_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_UNP_USER_TOTAL = prometheus_client.Gauge(
    "UNP_User_Total_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_UNP_USER_RATIO = prometheus_client.Gauge(
    "UNP_User_Ratio_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_ROUTING_LOCAL = prometheus_client.Gauge(
    "Routing_Table_Local_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_ROUTING_STATIC = prometheus_client.Gauge(
    "Routing_Table_Static_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_ROUTING_OSPF = prometheus_client.Gauge(
    "Routing_Table_Ospf_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_ROUTING_IBGP = prometheus_client.Gauge(
    "Routing_Table_Ibgp_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_ROUTING_EBGP = prometheus_client.Gauge(
    "Routing_Table_Ebgp_Entries", 'Metrics scraped with python', ['name', 'ip'])
SYSTEM_ROUTING_TOTAL = prometheus_client.Gauge(
    "Routing_Table_Total_Entries", 'Metrics scraped with python', ['name', 'ip'])
path = "/opt/ALE_Script/"

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()


class IPThread(threading.Thread):
    def __init__(self, threadID, ip):
        threading.Thread.__init__(self)
        if ip == "10.130.7.240":
            IPThread.port = 22
            IPThread.username = switch_user
            IPThread.password = "switch"
        else:
            IPThread.port = 22
            IPThread.username = switch_user
            IPThread.password = switch_password

        self.name = "Thread-{}".format(threadID)
        self.ip = str(ip)

        self.Auth = True

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self.ssh.connect(self.ip, IPThread.port,
                             IPThread.username, IPThread.password)
        except paramiko.ssh_exception.AuthenticationException:
            self.Auth = False
            self.ssh.close()
            self.ssh = False
            pass
        except paramiko.ssh_exception.NoValidConnectionsError:
            self.ssh.close()
            self.ssh = False
            pass
        except paramiko.ssh_exception.SSHException:
            self.ssh.close()
            self.ssh = False
            pass

    def run(self):
        print("Starting {} : ".format(self.name) + self.ip)
        if self.ssh:
            error_code = self.addMetrics()
        elif not self.Auth:
            # Exception Error Code 401 if SSH Authentication issue
            error_code = 401
        else:
            # Exception Error Code 404 if Device unreachable
            error_code = 404

        if error_code != 0:
            print("Error {} in {} (ip:{})".format(
                error_code, self.name, self.ip))

    def join(self):
        print("Ending " + self.name)
        return super().join()

    def addMetrics(self):
        try:  # Exception if no device is not reachable by SSH
            # NAME
            switch_cmd = "show system | grep Name"
            try:
                _, stdout, _ = self.ssh.exec_command(switch_cmd)
                output = stdout.read().decode('utf-8')
            except Exception:
                return 1
            name = re.findall(r"([A-Za-z0-9-]*),", output)[0]

            # MEMORY
            switch_cmd = "show health all memory"
            try:
                _, stdout, _ = self.ssh.exec_command(switch_cmd)
                output = stdout.read().decode('utf-8')
            except Exception:
                return 2
            matchs_mem = re.findall(
                r"Slot  (\d+?)\/ (\d+?) *(\d*?) ", output)
            for chassis, slot, mem in matchs_mem:
                try:

                    SYSTEM_MEM.labels(name=name, ip=self.ip,
                                      chassis=chassis, slot=slot).set(mem)

                except ValueError:
                    return 3

            # CPU
            switch_cmd = "show health all cpu"
            try:
                _, stdout, _ = self.ssh.exec_command(switch_cmd)
                output = stdout.read().decode('utf-8')
            except Exception:
                return 4
            matchs_cpu = re.findall(
                r"Slot  (\d+?)\/ (\d+?) *(\d*?) ", output)
            for chassis, slot, cpu in matchs_cpu:
                try:

                    SYSTEM_CPU.labels(name=name, ip=self.ip,
                                      chassis=chassis, slot=slot).set(cpu)

                except ValueError:
                    return 5

            # TEMP
            switch_cmd = "show temperature"
            try:
                _, stdout, _ = self.ssh.exec_command(switch_cmd)
                output = stdout.read().decode('utf-8')
            except Exception:
                return 6
            matchs_temp = re.findall(r"(\d*?)/CMMA *(\d*?) ", output)
            for chassis, temp in matchs_temp:
                try:

                    SYSTEM_TEMP.labels(name=name, ip=self.ip,
                                       chassis=chassis).set(temp)
                except ValueError:
                    return 7

            # ARP Entries
            switch_cmd = "show arp"
            try:
                _, stdout, _ = self.ssh.exec_command(switch_cmd)
                output = stdout.read().decode('utf-8')
            except Exception:
                return 8
            matchs_arp_entries = re.findall(r"Total (\d*) arp entries", output)

            for arp_entries in matchs_arp_entries:

                SYSTEM_ARP.labels(name=name, ip=self.ip).set(arp_entries)

            # MAC-Learning Entries
            switch_cmd = "show mac-learning"
            try:
                _, stdout, _ = self.ssh.exec_command(switch_cmd)
                output = stdout.read().decode('utf-8')
            except Exception:
                return 9
            matchs_mac_learning_bridging_entries = 0
            matchs_mac_learning_servicing_entries = 0
            matchs_mac_learning_filtering_entries = 0
            matchs_mac_learning_total_entries = 0
            matchs_mac_filtering_ratio_entries = 0
            count = dict(Counter(output.split()))
            try:
                matchs_mac_learning_bridging_entries = count['bridging']

                SYSTEM_MAC_BRIDGING.labels(name=name, ip=self.ip).set(
                    matchs_mac_learning_bridging_entries)

            except KeyError:
                pass
            try:
                matchs_mac_learning_servicing_entries = count['servicing']

                SYSTEM_MAC_SERVICING.labels(name=name, ip=self.ip).set(
                    matchs_mac_learning_servicing_entries)

            except KeyError:
                pass
            try:
                matchs_mac_learning_filtering_entries = count['filtering']

                SYSTEM_MAC_FILTERING.labels(name=name, ip=self.ip).set(
                    matchs_mac_learning_filtering_entries)
            except KeyError:
                pass

            # Ratio (number of MAC Filtering State / number of MAC Total) * 100
            try:
                matchs_mac_learning_total_entries = (
                    matchs_mac_learning_bridging_entries + matchs_mac_learning_servicing_entries + matchs_mac_learning_filtering_entries)
                matchs_mac_filtering_ratio_entries = (
                    matchs_mac_learning_filtering_entries / matchs_mac_learning_total_entries) * 100
                SYSTEM_MAC_FILTERING_RATIO.labels(name=name, ip=self.ip).set(
                    matchs_mac_filtering_ratio_entries)
            except KeyError:
                pass
            except ZeroDivisionError:
                pass

            # UNP User metrics
            switch_cmd = "show unp user"
            try:
                _, stdout, _ = self.ssh.exec_command(switch_cmd)
                output = stdout.read().decode('utf-8')
            except Exception:
                return 10
            matchs_unp_user_active_entries = 0
            matchs_unp_user_block_entries = 0
            matchs_unp_user_total_entries = 0
            matchs_unp_user_ratio_entries = 0
            count = dict(Counter(output.split()))
            try:
                matchs_unp_user_active_entries = count['Active']
                SYSTEM_UNP_USER_ACTIVE.labels(name=name, ip=self.ip).set(
                    matchs_unp_user_active_entries)

            except KeyError:
                pass

            try:
                matchs_unp_user_block_entries = count['Block']
                SYSTEM_UNP_USER_BLOCK.labels(name=name, ip=self.ip).set(
                    matchs_unp_user_block_entries)

            except KeyError:
                pass

            try:
                matchs_unp_user_total_entries = count['Bridge']
                SYSTEM_UNP_USER_TOTAL.labels(name=name, ip=self.ip).set(
                    matchs_unp_user_total_entries)
            except KeyError:
                pass

            # Ratio (number of UNP User Block State / number of UNP User Total) * 100
            try:
                matchs_unp_user_ratio_entries = (
                    matchs_unp_user_block_entries / matchs_unp_user_total_entries) * 100
                print(matchs_unp_user_ratio_entries)
                SYSTEM_UNP_USER_RATIO.labels(name=name, ip=self.ip).set(
                    matchs_unp_user_ratio_entries)
            except KeyError:
                pass
            except ZeroDivisionError:
                pass

            # Routing Table metrics
            switch_cmd = "show ip routes"
            try:
                _, stdout, _ = self.ssh.exec_command(switch_cmd)
                output = stdout.read().decode('utf-8')
            except Exception:
                return 11

            matchs_routing_table_total_entries = 0
            try:
                matchs_routing_table_total_entries = re.findall(
                    r" Total (\d*) routes", output)
                for routing_table_total_entries in matchs_routing_table_total_entries:
                    SYSTEM_ROUTING_TOTAL.labels(name=name, ip=self.ip).set(
                        routing_table_total_entries)

            except KeyError:
                pass

            matchs_routing_table_local_entries = 0
            matchs_routing_table_static_entries = 0
            matchs_routing_table_ospf_entries = 0
            matchs_routing_table_ibgp_entries = 0
            matchs_routing_table_ebgp_entries = 0
            count = dict(Counter(output.split()))
            try:
                matchs_routing_table_local_entries = count['LOCAL']
                SYSTEM_ROUTING_LOCAL.labels(name=name, ip=self.ip).set(
                    matchs_routing_table_local_entries)
            except KeyError:
                pass

            try:
                matchs_routing_table_static_entries = count['STATIC']
                SYSTEM_ROUTING_STATIC.labels(name=name, ip=self.ip).set(
                    matchs_routing_table_static_entries)

            except KeyError:
                pass

            try:
                matchs_routing_table_ospf_entries = count['OSPF']

                SYSTEM_ROUTING_OSPF.labels(name=name, ip=self.ip).set(
                    matchs_routing_table_ospf_entries)

            except KeyError:
                pass

            try:
                matchs_routing_table_ibgp_entries = count['IBGP']

                SYSTEM_ROUTING_IBGP.labels(name=name, ip=self.ip).set(
                    matchs_routing_table_ibgp_entries)
            except KeyError:
                pass

            try:
                matchs_routing_table_ebgp_entries = count['EBGP']

                SYSTEM_ROUTING_EBGP.labels(name=name, ip=self.ip).set(
                    matchs_routing_table_ebgp_entries)

            except KeyError:
                pass

            # ADD HERE

            self.ssh.close()
            return 0
        except Exception as e:
            print(e)


if __name__ == '__main__':
    prometheus_client.start_http_server(9999)

    while True:
        threads = []
        count = 0
        ips_address = list()
        with open(path + 'Devices.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=';')
            line = 0
            for row in csv_reader:
                if line == 0:
                    line = 1
                    continue
                ips_address.append(str(row[1]))
        # Start all Threads
        for ipaddr in ips_address:
            try:
                print("TEST " + ipaddr)
                output = subprocess.check_output(
                    ["ping", "-{}".format('n' if platform.system().lower() == "windows" else 'c'), "1", "{}".format(ipaddr)], stderr=subprocess.DEVNULL, timeout=40
                )
                if not re.search(r"TTL|ttl", str(output)):
                    continue
            except subprocess.CalledProcessError:
                continue

            t = IPThread(count, ipaddr)
            t.start()
            threads.append(t)
            time.sleep(0.1)
            count += 1

        # Wait for all threads to complete
        for t in threads:
            t.join()

        time.sleep(300)
