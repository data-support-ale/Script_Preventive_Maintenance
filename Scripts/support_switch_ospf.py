#!/usr/local/bin/python3.7

import sys
import os
import re
import json
from support_tools_OmniSwitch import get_credentials
from time import strftime, localtime, sleep
from support_send_notification import send_message
from database_conf import *

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

# Log sample
# OS6860E_VC_Core swlogd ospf_nbr.c ospfNbrStateMachine 0 ospf_0 STATE EVENT: CUSTLOG CMM OSPF neighbor state change for 172.25.136.2, router-id 172.25.136.2: FULL to DOWN

last = ""
with open("/var/log/devices/lastlog_ospf.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_ospf.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_ospf.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ip = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_ospf.json empty")
        exit()
    except IndexError:
        print("Index error in regex")
        exit()

    try:    
        neighbor_ip, router_id, initial_state, final_state = re.findall(r"CUSTLOG CMM OSPF neighbor state change for (.*?), router-id (.*?): (.*?) to (.*)", msg)[0]
    except IndexError:
        print("Index error in regex")
        exit()
if "FULL" in final_state:
    notif = ("Preventive Maintenance Application - OSPF Neighbor state change on OmniSwitch {0} / {1}.\n\nDetails:\n- Router-ID: {2}\n- Neighbor-ID {3}\n- Initial State: {4}\n- Final State: {5}.").format(host,ip,router_id,neighbor_ip,initial_state,final_state)
    send_message(notif, jid)
else:
    notif = ("Preventive Maintenance Application - OSPF Neighbor state change on OmniSwitch {0} / {1}.\n\nDetails:\n- Router-ID: {2}\n- Neighbor-ID {3}\n- Initial State: {4}\n- Final State: {5}\nPlease check the OSPF Neighbor node connectivity.").format(host,ip,router_id,neighbor_ip,initial_state,final_state)
    send_message(notif, jid)   

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                    "OSPF_Neighbor_IP": neighbor_ip, "IP": ip, "OSPF_Router_ID": router_id, "State": final_state}, "fields": {"count": 1}}])
except UnboundLocalError as error:
    print(error)
    sys.exit()
except Exception as error:
    print(error)
    pass 
