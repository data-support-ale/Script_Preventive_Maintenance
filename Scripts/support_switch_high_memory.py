#!/usr/local/bin/python3.7

import logging

from time import  strftime, localtime, sleep
import sys
import os
import datetime
from support_tools_OmniSwitch import get_credentials, get_tech_support_sftp, send_file, ssh_connectivity_check
from support_send_notification import send_message
import subprocess
import requests
import paramiko
import json
import pysftp
from database_conf import *

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

date = datetime.date.today()
date_hm = datetime.datetime.today()

last = ""
with open("/var/log/devices/lastlog_high_memory.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_high_memory.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_high_memory.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
        l = []
        l.append('/code ')
        l.append(msg)
        message_reason = ''.join(l)
    except json.decoder.JSONDecodeError as error:
        print(error)
        print("File /var/log/devices/lastlog_high_memory.json empty")
        exit()

print(ipadd)
print(host)
info = "A High Memory is noticed on OmniSwitch {0}/{1}and we are collecting logs on Server {2} /tftpboot/ directory".format(host,ipadd,ip_server)
#send_message(info,jid)
try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Result": "Init"}, "fields": {"count": 1}}])
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass 


text = "More logs about the switch : {0} \n\n\n".format(ipadd)

l_switch_cmd = []
l_switch_cmd.append('echo \"date\" | su')
l_switch_cmd.append("show virtual-chassis topology")
l_switch_cmd.append("show chassis")
l_switch_cmd.append("show system")
l_switch_cmd.append("show health")
l_switch_cmd.append("show health all cpu")
l_switch_cmd.append("show health all memory")
l_switch_cmd.append("show health all rx")
l_switch_cmd.append("show health all txrx")
l_switch_cmd.append('echo \"top -d 5 -n 5\" | su')
l_switch_cmd.append('echo \"free -m\" | su')
sleep(2)
l_switch_cmd.append('echo \"free -m\" | su')
l_switch_cmd.append('echo \"cat \/proc\/meminfo\" | su')
sleep(2)
l_switch_cmd.append('echo \"cat \/proc\/meminfo\" | su')
sleep(2)
l_switch_cmd.append('echo \"top -b -n 1 | head\" | su')
sleep(2)
l_switch_cmd.append('echo \"top -b -n 1 | head\" | su')
sleep(2)
l_switch_cmd.append('echo \"top -b -n 1 | head\" | su')
sleep(2)
l_switch_cmd.append('echo \"top -b -n 1 | head\" | su')
sleep(2)
l_switch_cmd.append('echo \"top -b -n 1 | head\" | su')

for switch_cmd in l_switch_cmd:
        try:
            output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output_decode)
            else:
                exception = "Timeout"
                info = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                os.system('logger -t montag -p user.info ' + info)
                send_message(info, jid)
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                except UnboundLocalError as error:
                    print(error)
                except Exception as error:
                    print(error)
                    pass 
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
        except subprocess.SubprocessError as exception:
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
date = datetime.date.today()
date_hm = datetime.datetime.today()

filename = "{0}_{1}-{2}_{3}_high_memory_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
filename_path = ('/opt/ALE_Script/{0}.txt').format(filename)
f_logs = open(filename_path, 'w')
f_logs.write(text)
f_logs.close()
category = "high_memory"

filename='{0}_logs.txt'.format(host)
remoteFilePath = '/flash/python/{0}'.format(filename)
localFilePath = "/tftpboot/{0}_{1}-{2}_{3}_{4}_high_memory".format(date,date_hm.hour,date_hm.minute,ipadd,filename) 

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Result": "Commands executed on Switch"}, "fields": {"count": 1}}])
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass 

subject = ("Preventive Maintenance Application - High Memory issue detected on switch: {0}").format(ipadd)
action = ("A High Memory issue has been detected in switch(Hostname: {0}) and we have collected logs as well as Tech-Support eng complete archive").format(host)
result = "Find enclosed to this notification the log collection for further analysis"
category = "high_memory"

### TECH-SUPPORT ENG COMPLETE ###
get_tech_support_sftp(switch_user, switch_password, host, ipadd)

send_file(filename_path, subject, action, result,category)

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Result": "Logs collected"}, "fields": {"count": 1}}])
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass 