#!/usr/local/bin/python3.7

import logging

from time import  strftime, localtime, sleep
import sys
import os
import datetime
from support_tools_OmniSwitch import get_credentials, get_tech_support_sftp, get_file_sftp
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
with open("/var/log/devices/lastlog_high_cpu.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_high_cpu.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_high_cpu.json", "r", errors='ignore') as log_file:
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
        print("File /var/log/devices/lastlog_high_cpu.json empty")
        exit()

print(ipadd)
print(host)
#{"@timestamp":"2021-11-22T21:57:06+01:00","type":"syslog_json","relayip":"10.130.7.243","hostname":"sw5-bcb","message":"<134>Nov 22 21:57:06 OS6860E_VC_Core swlogd healthCmm main EVENT: CUSTLOG CMM NI 1/1 rising above CPU threshold","end_msg":""}
info = "A High CPU is noticed and we are collecting logs on Server {0} /tftpboot/ directory".format(ip_server)
send_message(info,jid)
cmd = "python3 /flash/python/get_logs_high_cpu.py"

#### Old method ####
#text = "More logs about the switch : {0} \n\n\n".format(ipadd)
#for switch_cmd in l_switch_cmd:
#   cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password,switch_user,ipadd,switch_cmd)
#   run=cmd.split()
#   p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
#   out, err = p.communicate()
#   out=out.decode('UTF-8').strip()

#   text = "{0}{1}: \n{2}\n\n".format(text,switch_cmd,out) 
try:
      p = paramiko.SSHClient()
      p.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      p.connect(ipadd, port=22, username=switch_user, password=switch_password)
      logging.info(' Connecting to OmniSwitch ' + ipadd)
except paramiko.ssh_exception.AuthenticationException:
        print("Authentication failed - please enter valid user name and password")
        info = ("SSH Authentication failed when connecting to OmniSwitch {0}, we cannot collect logs").format(ipadd)
        send_message(info,jid)
        sys.exit(0)

except paramiko.ssh_exception.NoValidConnectionsError:
        print("Device unreachable")
        info = ("OmniSwitch {0} is unreachable, we cannot collect logs").format(ipadd)
        send_message(info,jid)
        sys.exit(0)

stdin, stdout, stderr = p.exec_command(cmd)
exception = stderr.readlines()
exception = str(exception)
connection_status = stdout.channel.recv_exit_status()
if connection_status != 0:
        info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd,exception)
        send_message(info,jid)
        sys.exit(2)
sleep(2)
filename='{0}_logs.txt'.format(host)
remoteFilePath = '/flash/python/{0}'.format(filename)
localFilePath = "/tftpboot/{0}_{1}-{2}_{3}_{4}".format(date,date_hm.hour,date_hm.minute,ipadd,filename) 
### Old method for collecting logs by sftp
#cnopts = pysftp.CnOpts()
#cnopts.hostkeys = None
#with pysftp.Connection(host=ipadd, username="admin", password="switch",cnopts=cnopts) as sftp:
#        sftp.get(remoteFilePath, localFilePath)

sleep(2)
#### Download log file by SFTP with Paramiko ###
get_file_sftp(switch_user, switch_password, ipadd, remoteFilePath, localFilePath)

info = "Process finished and logs downloaded"
os.system('logger -t montag -p user.info Process finished and logs downloaded for High CPU issue ')
print(localFilePath)

### TECH-SUPPORT ENG COMPLETE ###
get_tech_support_sftp(switch_user, switch_password, host, ipadd)

jid1="j_9403700392@openrainbow.com"
url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Test_EMEA"
headers = {  'Content-type':"text/plain",'Content-Disposition': "attachment;filename=port_flapping.log", 'jid1': '{0}'.format(jid),'toto': '{0}'.format(info)}
files = {'file': open(localFilePath,'r')}
response = requests.post(url,files=files, headers=headers)