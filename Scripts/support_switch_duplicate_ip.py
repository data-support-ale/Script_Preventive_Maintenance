#!/usr/local/bin/python3.7

from operator import contains
import sys
import os
import re
import json
import paramiko
import threading
from support_tools_OmniSwitch import isEssential, ssh_connectivity_check, file_setup_qos, format_mac, get_credentials, add_new_save, check_save, script_has_run_recently, send_file
from time import strftime, localtime
from support_send_notification import send_message, send_message_request_advanced, send_message_request
from database_conf import *

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()


def enable_qos_ddos(user, password, ipadd, ipadd_ddos):

    file_setup_qos(ipadd_ddos)

    remote_path = '/flash/working/configqos'
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ipadd, username=user, password=password, timeout=20.0)
        sftp = ssh.open_sftp()
        # In case of SFTP Get timeout thread is closed and going into Exception
        try:
            filename = "/opt/ALE_Script/configqos"
            th = threading.Thread(
                target=sftp.put, args=(filename, remote_path))
            th.start()
            th.join(120)
        except IOError:
            exception = "File error or wrong path"
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                    "Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass
        except Exception:
            exception = "SFTP Get Timeout"
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                    "Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass
            sys.exit()
    except paramiko.ssh_exception.AuthenticationException:
        exception = "SFTP Get Timeout"
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                "Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass

    cmd = "configuration apply ./working/configqos "
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)


# Sample log
# {"@timestamp":"2022-01-05T12:14:46+01:00","type":"syslog_json","relayip":"10.130.7.247","hostname":"os6860","message":"<13>Jan  5 12:14:46 OS6860 ConsLog [slot 1\/1] Wed Jan  5 12:14:46  ipni arp WARN duplicate IP address 10.130.7.247 from port 1\/1\/9 eth addr 38f3ab:592a7e","end_msg":""}
last = ""
with open("/var/log/devices/lastlog_dupip.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_dupip.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_dupip.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ip = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_dupip.json empty")
        exit()
    except IndexError:
        print("Index error in regex")
        exit()
    if "duplicate" in msg:
        try:
            ip_dup, port, mac = re.findall(r"duplicate IP address (.*?) from port (.*?) eth addr (.*)", msg)[0]
        except IndexError:
            print("Index error in regex")
            exit()
    # CORE swlogd ipni arp INFO: arp info overwritten for 172.16.29.30 by 78e3b5:054b08 port Lag 1
    elif "overwritten" in msg:
        try:
            ip_dup, mac, port = re.findall(r"arp info overwritten for (.*?) by (.*?) port (.*)", msg)[0]
        except IndexError:
            print("Index error in regex")
            exit()
    else:
        print("No pattern match")
        exit()         
    mac = format_mac(mac)

function = "duplicate_ip"
if script_has_run_recently(300,ip,function):
    print('you need to wait before you can run this again')
    os.system('logger -t montag -p user.info Executing script exit because executed within 5 minutes time period')
    exit()

# always 1
#never -1
# ? 0
save_resp = check_save(ip, port, "duplicate")

if save_resp == "0":
    if not ("Lag")in port: 
        feature = "Disable port " + port
        notif = "An IP address duplication (" + ip_dup + ") on port " + port + " of OmniSwitch " + ip + "/" + host + " has been detected. Do you want to blacklist the MAC Address: " + mac + " ?"
        answer = send_message_request_advanced(notif, jid,feature)
        print(answer)

    else:
        notif = "An IP address duplication (" + ip_dup + ") on port " + port + " of OmniSwitch " + ip + "/" + host + " has been detected. Do you want to blacklist the MAC Address: " + mac + " ?"
        answer = send_message_request(notif, jid)  

    if isEssential(ip_dup):
        answer = "0"
        info = "An IP duplication has been detected on your network that involves essential IP Address {} therefore we do not proceed further".format(ip_dup)
        send_message(info,jid)
        sys.exit()

    if "e8:e7:32" in format_mac(mac):
        answer = "0"
        info = "An IP duplication has been detected on your network that involves an Alcatel OmniSwitch chassis/interfaces MAC-Address therefore we do not proceed further".format(ip_dup)
        send_message(info,jid)
        sys.exit()
       
    if answer == "2":
        add_new_save(ip, port, "duplicate", choice="always")
        answer = '1'
    elif answer == "0":
        add_new_save(ip, port, "duplicate", choice="never")
elif save_resp == "-1":
    try:
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ip, "IP_dup": ip_dup, "mac": mac}, "fields": {"count": 1}}])
        sys.exit()   
    except UnboundLocalError as error:
       print(error)
       sys.exit()
    except Exception as error:
        print(error)
        sys.exit()
else:
    answer = '1'

if answer == '1':
    os.system('logger -t montag -p user.info Process terminated')
    enable_qos_ddos(switch_user, switch_password, ip, mac)
    if jid != '':
        info = "Log of device : {0}".format(ip)
        send_file(info, jid, ip)
        info = "An IP Address duplication has been detected on your network and QOS policy has been applied to prevent access for the MAC Address {0} to device {1}".format(mac, ip)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                "IP": ip, "IP_dup": ip_dup, "mac": mac}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass
## Value 3 when we return advanced value like Disable port x/x/x
elif answer == '3':
    os.system('logger -t montag -p user.info Process terminated')
    # DISABLE Port
    cmd = "interfaces port " + port + " admin-state disable"
    ssh_connectivity_check(switch_user, switch_password, ip, cmd)
    filename_path = "/var/log/devices/" + host + "/syslog.log"
    category = "ddos"
    subject = "An IP Address duplication has been detected:".format(host, ip)
    action = "An IP Address duplication has been detected on your network and interface port {0} is disabled to prevent access to OmniSwitch {2} / {3}".format(port,ip_dup, host, ip)
    result = "Find enclosed to this notification the log collection"
    send_file(filename_path, subject, action, result, category)
    try:
         write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
            "IP": ip, "IP_dup": ip_dup, "mac": mac}, "fields": {"count": 1}}])
    except UnboundLocalError as error:
        print(error)
    except Exception as error:
        print(error)
        pass