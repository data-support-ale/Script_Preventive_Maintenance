#!/usr/bin/env python3

import sys
import os
import re
import json
from support_tools import enable_debugging, disable_debugging, disable_port, extract_ip_port, check_timestamp, get_credentials,extract_ip_ddos,disable_debugging_ddos,enable_qos_ddos,get_id_client,get_server_log_ip
from time import strftime, localtime, sleep
from support_send_notification import send_message, send_mail,send_file


# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get informations from logs.
switch_user, switch_password, jid, gmail_user, gmail_password, mails, ip_server = get_credentials()
ip_server_log = get_server_log_ip()
send_file("TEST",jid, "10.130.7.247", "")
