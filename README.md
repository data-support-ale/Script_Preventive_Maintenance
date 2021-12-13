# Script_Preventive_Maintenance

# Rsyslog - what is it?

Rsyslog is a rocket-fast system for log processing.

It offers high-performance, great security features and a modular design. While it started as a regular syslogd, rsyslog has evolved into a kind of swiss army knife of logging, being able to accept inputs from a wide variety of sources, transform them, and output to the results to diverse destinations.

Rsyslog can deliver over one million messages per second to local destinations when limited processing is applied (based on v7, December 2013). Even with remote destinations and more elaborate processing the performance is usually considered "stunning".

# Project Overview
The purpose of this project is to provide scripting for automation of several tasks like:
- automatic log collection
- Stellar AP upgrade
- automatic incidence resolution
- notifications by email or rainbow

We use Linux Debian or Raspbian Distributions

# Checklist to verify that Setup is working fine:
###### 1. Add CLI Command ```swlog output socket <ip_address> <port> vrf <vrf_name>```
Please use the **UDP** port **10514** as this is set on Rsyslog thru the Setup.sh script:  ```swlog output socket <ip_address> 10514```

###### 2. Check if syslogs are received by application, execute command: ```tail -f /var/log/syslog``` and if application is listening on UDP port 10514
```
admin-support@debian2:~$ tail -f /var/log/syslog
Dec 13 10:16:06 RZW-Core swlogd bcmd rpcs DBG2: _bcm_server_rpc_rcv 431: Reac Recv len 12, mlen 206
Dec 13 10:16:06 RZW-Core swlogd bcmd rpcs DBG2: _bcm_server_rpc_rcv 427: Reac Recv len 218, mlen 206 socket 49
Dec 13 10:16:06 RZW-Core swlogd bcmd rpcs DBG2: bcm_rpc_reply: sending data @0x540005ac len 360 to socket 49

admin-support@debian2:/opt/ALE_Script$ netstat -anp | grep 10514
(Not all processes could be identified, non-owned process info
 will not be shown, you would have to be root to see it all.)
udp        0      0 0.0.0.0:10514           0.0.0.0:*
```
###### 3. Check if syslogs are stored in ```/var/log/devices/<switch_system_name>/syslog.log```, execute command ```ls -la /var/log/devices/```
```
admin-support@debian2:~$ ls -la /var/log/devices/
drwxr-xr-x  2 root root      4096 Dec 13 00:09 RZW-Core
admin-support@debian2:~$ ls -la /var/log/devices/RZW-Core/
total 376000
drwxr-xr-x  2 root root      4096 Dec 13 00:09 .
drwxr-xr-x 48 root root     45056 Dec 13 10:11 ..
-rw-r--r--  1 root adm  265660567 Dec 13 10:18 syslog.log
-rw-r--r--  1 root adm   10295896 Dec  4 00:09 syslog.log.2021-12-04.gz
-rw-r--r--  1 root adm   10309944 Dec  5 00:08 syslog.log.2021-12-05.gz
```
###### 4. Check if the Rsyslog service is running: ```sudo systemctl status rsyslog```
```
admin-support@debian2:~$ sudo systemctl status rsyslog
[sudo] password for admin-support:
● rsyslog.service - System Logging Service
   Loaded: loaded (/lib/systemd/system/rsyslog.service; enabled; vendor preset: enabled)
   Active: active (running) since Fri 2021-12-10 18:44:06 CET; 2 days ago
```
Here a Child with ID will be created each time a python script is executed

###### 5. Check if the scripts are executed, every scripts are logged thru syslog by using a tag **"montag"** and printed into ```/var/log/devices/script_execution.log file``` . 
```
admin-support@debian2:/var/log/devices$ tail -f /var/log/devices/script_execution.log
Dec 13 10:11:16 debian2 montag: Executing script /opt/ALE_Script/support_switch_port_flapping.py
Dec 13 10:11:18 debian2 montag: Executing script /opt/ALE_Script/support_switch_port_flapping.py
Dec 13 10:11:56 debian2 montag: Executing script /opt/ALE_Script/support_switch_port_flapping.py
```

###### 6. Check if the python scripts are executing without errors/exceptions:
Note: several scripts open a json file for processing data and find the ipaddress (column: relayip) the hostname, and additionnal data like port, vcid, power supply ID, therefore if json file is empty the script won't execute

You can edit or create the ```/var/log/devices/lastlog_auth_fail.json``` file with content:
```
admin-support@debian2:/opt/ALE_Script$ cat /var/log/devices/lastlog_authfail.json
{"@timestamp":"2021-12-11T11:04:09+01:00","type":"syslog_json","relayip":"10.130.7.244","hostname":"lan-6860n-2","message":"<134>Dec 11 11:04:09 LAN-6860N-2 swlogd SES MIP EVENT: CUSTLOG CMM Authentication failure detected: user admin","end_msg":""}
```
Then execute the script ```sudo python3 support_switch_auth_fail.py```

###### 7. Check if the application has connectivity with VNA, you can modify the test.py script as below and execute with command ```sudo python3 /opt/ALE_Script/test.py NAR```, it will call VNA workflow thru a HTTPS REST-API and will send message "NBD Preventive Maintenance - This is a test!" on your Rainbow bubble
```
admin-support@debian2:/opt/ALE_Script$ cat test.py
#!/usr/bin/env python3

import sys
import os
import re
import json
from support_tools import enable_debugging, disable_debugging, disable_port, extract_ip_port, check_timestamp, get_credentials,extract_ip_ddos,disable_debugging_ddos,enable_qos_ddos,get_id_client,get_server_log_ip
from time import strftime, localtime, sleep
from support_send_notification import send_message, send_mail,send_file
import requests

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user, switch_password, jid, gmail_user, gmail_password, mails, ip_server = get_credentials()
ip_server_log = get_server_log_ip()
company=0

## If we put argument when calling the script we can test different Workflows (companies)
if sys.argv[1] != 0:
    company = sys.argv[1]
    print(company)
    info = "NBD Preventive Maintenance - This is a test!"
    url = ("https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Classic_{0}").format(company)
    headers = {'Content-type': 'application/json', "Accept-Charset": "UTF-8", 'jid1': '{0}'.format(jid), 'toto': '{0}'.format(info),'Card': '0'}
    response = requests.get(url, headers=headers)
else:
    send_file("TEST",jid, "10.130.7.247", "")
```
Example:
```
admin-support@debian2:/opt/ALE_Script$ sudo python3 /opt/ALE_Script/test.py EMEA
[sudo] password for admin-support:
/usr/local/lib/python3.5/dist-packages/paramiko/transport.py:33: CryptographyDeprecationWarning: Python 3.5 support will be dropped in the next release of cryptography. Please upgrade your Python.
  from cryptography.hazmat.backends import default_backend
EMEA
```
###### 8. About VNA, I created for you the workflow "Preventive_maintenance_Calabasas", basic things to check:
- on Rainbow IM check if the bubble is correct, shall be "Tech_support_notif_NAR"
- on Send Email check if the email destination are correct, user group or user's email address

###### 9. Basic script for collecting CLI command output on OmniSwitch with an example how to get the port number if json file content is ```/var/log/devices/get_log_switch.json```:
```
{"@timestamp":"2021-12-08T17:17:13+01:00","type":"syslog_json","relayip":"10.130.7.243","hostname":"rzw-core","message":"<134>Dec  8 17:17:13 RZW-Core swlogd portMgrNi main INFO: : [pmnHALLinkStatusCallback:206] LINKSTS 1\/1\/53A DOWN (gport 0x40) Speed 40000 Duplex FULL","end_msg":""}
```
- ###### **9.a** first create the rule on /etc/rsyslog.conf with the pattern you want to match and trigger python execution:
```
if $msg contains 'specific log generated when issue occurs' then {
       action(type="omfile" DynaFile="deviceloghistory" template="json_syslog" DirCreateMode="0755" FileCreateMode="0755")
       action(type="omfile" DynaFile="deviceloggetlogswitch" template="json_syslog" DirCreateMode="0755" FileCreateMode="0755")
       action(type="omprog" binary="/opt/ALE_Script/myscript.py" queue.type="LinkedList" queue.size="1" queue.workerThreads="1")
       stop
}
```
- ###### **9.b** restart Rsyslog and check status
```
sudo systemctl restart rsyslog
sudo systemctl status rsyslog
```
- ###### **9.c** create your script /opt/ALE_Script/myscript.py. Script open json file ```/var/log/devices/get_log_switch.json```, get switch ip address, switch hostname, port number with function get_port()
```
#!/usr/bin/env python3

import sys
import os
import getopt
import json
import logging
import datetime
from time import gmtime, strftime, localtime,sleep
from support_tools import get_credentials,get_server_log_ip,get_jid,get_mail,send_python_file_sftp,get_file_sftp
from support_send_notification import send_message,send_file,send_mail
import subprocess
import re
import pysftp
import requests
import paramiko

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
date = datetime.date.today()
date_hm = datetime.datetime.today()

switch_user, switch_password, jid, gmail_user, gmail_password, mails,ip_server_log = get_credentials()
filename = 'tech_support_complete.tar'

last = ""
with open("/var/log/devices/get_log_switch.json", "r") as log_file:
   for line in log_file:
      last = line

with open("/var/log/devices/get_log_switch.json", "w") as log_file:
   log_file.write(last)

with open("/var/log/devices/get_log_switch.json", "r") as log_file:
   log_json = json.load(log_file)
   ipadd = log_json["relayip"]
   host = log_json["hostname"]
   msg = log_json["message"]
   print(msg)

print("Switch IP Address is: " + ipadd)
print("Switch Hostname is: " + host)
print("Syslog raw message: " + msg)

pattern = ""
if len(sys.argv) > 1:
   pattern = sys.argv[1]
   print(pattern)
   info = ("We received following pattern from RSyslog {0}").format(pattern)
   os.system('logger -t montag -p user.info ' + info)

def get_port():
   with open("/var/log/devices/get_log_switch.json", "r") as log_file:
      log_json = json.load(log_file)
      ipadd = log_json["relayip"]
      host = log_json["hostname"]
      msg = log_json["message"]
      print(msg)
      port = re.findall(r"LINKSTS (.*?) DOWN", msg)[0]
      port = port.replace("\"", "",3)
      port = port.replace("\\", "",3)
      print(port)
      return port

try:
   p = paramiko.SSHClient()
   p.set_missing_host_key_policy(paramiko.AutoAddPolicy())
   p.connect(ipadd, port=22, username="admin", password="switch")
except paramiko.ssh_exception.AuthenticationException:
   print("Authentication failed enter valid user name and password")
   info = ("SSH Authentication failed when connecting to OmniSwitch {0}, we cannot collect logs").format(ipadd)
   os.system('logger -t montag -p user.info {0}').format(info)
   send_message(info,jid)
   sys.exit(0)
except paramiko.ssh_exception.NoValidConnectionsError:
   print("Device unreachable")
   logging.info(runtime + ' SSH session does not establish on OmniSwitch ' + ipadd)
   info = ("OmniSwitch {0} is unreachable, we cannot collect logs").format(ipadd)
   os.system('logger -t montag -p user.info {0}').format(info)
   send_message(info,jid)
   sys.exit(0)
cmd = ("rm -rf {0}").format(filename)
stdin, stdout, stderr = p.exec_command(cmd)
exception = stderr.readlines()
exception = str(exception)
connection_status = stdout.channel.recv_exit_status()
if connection_status != 0:
   info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd,exception)
   send_message(info,jid)
   os.system('logger -t montag -p user.info ' + info)
   sys.exit(2)

stdin, stdout, stderr = p.exec_command("show tech-support eng complete")
exception = stderr.readlines()
exception = str(exception)
connection_status = stdout.channel.recv_exit_status()
if connection_status != 0:
   info = ("\"The show tech support eng complete\" command on OmniSwitch {0} failed - {1}").format(ipadd,exception)
   send_message(info,jid)
   os.system('logger -t montag -p user.info ' + info)
   sys.exit(2)

cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2}  ls | grep {3}".format(switch_password,switch_user,ipadd,filename)
run=cmd.split()
out=''
i=0
while not out:
   print(" Tech Support file creation under progress.", end="\r")
   sleep(2)
   print(" Tech Support file creation under progress..", end="\r")
   sleep(2)
   print(" Tech Support file creation under progress...", end="\r")
   print(i)
   sleep(2)
   p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
   out, err = p.communicate()
   out=out.decode('UTF-8').strip()
   if i > 20:
      print("Tech Support file creation timeout")
      exit()

f_filename= "/tftpboot/{0}_{1}-{2}_{3}_{4}".format(date,date_hm.hour,date_hm.minute,ipadd,filename)
get_file_sftp(switch_user,switch_password,ipadd,filename)

####
port = get_port()
print("port number is : " + port)

##########################Get More LOGS########################################
text = "More logs about the switch : {0} \n\n\n".format(ipadd)

l_switch_cmd = []
l_switch_cmd.append("show interfaces")
l_switch_cmd.append("show system")
l_switch_cmd.append("show chassis")
l_switch_cmd.append("show unp user")
l_switch_cmd.append("show lanpower slot 1/1")
l_switch_cmd.append("show interfaces port " + port)

for switch_cmd in l_switch_cmd:
   cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password,switch_user,ipadd,switch_cmd)
   output=subprocess.check_output(cmd,stderr=subprocess.DEVNULL, shell=True)
   output=output.decode('UTF-8').strip()
   text = "{0}{1}: \n{2}\n\n".format(text,switch_cmd,output)

date = datetime.date.today()
date_hm = datetime.datetime.today()

filename= "{0}_{1}-{2}_{3}_logs".format(date,date_hm.hour,date_hm.minute,ipadd)
f_logs = open('/opt/ALE_Script/{0}.txt'.format(filename),'w')
f_logs.write(text)
f_logs.close()
###############################################################################

if jid !='':
         info = "A Pattern {1} has been detected in switch(IP : {0}) syslogs. A snapshot has been sent in the directory /tftpboot/ on syslog server".format(ipadd,pattern)
         send_message(info,jid)
         send_message(msg,jid)

open('/var/log/devices/get_log_switch.json','w').close()
```

When executing the script:
```
admin-support@debian2:/opt/ALE_Script$ sudo python3 /opt/ALE_Script/myscript.py
/usr/local/lib/python3.5/dist-packages/paramiko/transport.py:33: CryptographyDeprecationWarning: Python 3.5 support will be dropped in the next release of cryptography. Please upgrade your Python.
  from cryptography.hazmat.backends import default_backend
<134>Dec  8 17:17:13 RZW-Core swlogd portMgrNi main INFO: : [pmnHALLinkStatusCallback:206] LINKSTS 1/1/53A DOWN (gport 0x40) Speed 40000 Duplex FULL
Switch IP Address is: 10.130.7.243
Switch Hostname is: rzw-core
Syslog raw message: <134>Dec  8 17:17:13 RZW-Core swlogd portMgrNi main INFO: : [pmnHALLinkStatusCallback:206] LINKSTS 1/1/53A DOWN (gport 0x40) Speed 40000 Duplex FULL
0Tech Support file creation under progress...
0Tech Support file creation under progress...
<134>Dec  8 17:17:13 RZW-Core swlogd portMgrNi main INFO: : [pmnHALLinkStatusCallback:206] LINKSTS 1/1/53A DOWN (gport 0x40) Speed 40000 Duplex FULL
1/1/53A
port number is : 1/1/53A
```

> Tech support eng complete is collected from switch and stored into ```/tftpboot/``` directory on Application:
```
admin-support@debian2:/tftpboot$ ls -la /tftpboot/
-rw-r--r--  1 root          root          38139392 Dec 13 11:24 2021-12-13_11-24_10.130.7.243_tech_support_complete.tar
```
> CLI Commands outputs are collected in file <date><time><switch_ipadd>_logs.txt in **/opt/ALE_Script directory**:
```
admin-support@debian2:/opt/ALE_Script$ ls -la *.txt
-rw-r--r-- 1 root          root          230463 Dec 13 11:24 2021-12-13_11-24_10.130.7.243_logs.txt
```
