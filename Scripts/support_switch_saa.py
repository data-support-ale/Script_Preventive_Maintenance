#!/usr/local/bin/python3.7

from distutils.log import info
import sys
import os
import json
from time import strftime, localtime
from support_tools_OmniSwitch import get_credentials, send_file, ssh_connectivity_check
from support_send_notification import send_message
from database_conf import *
import re

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

last = ""
with open("/var/log/devices/lastlog_saa.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_saa.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_saa.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_saa.json empty")
        exit()
    except IndexError:
        print("Index error in regex")
        exit()

    # Sample log
    # OS6900_VC swlogd saaCmm sm-proto INFO: saa_OS6860N_Aijaz - Iteration packet loss 4\/0
    if "Iteration packet loss" in msg:
        try:
            saa_name = re.findall(r"INFO: (.*?) - Iteration packet loss", msg)[0]
            cmd = "show saa statistics aggregate"
            output = ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)

            info = ("Service Assurance Agent - SAA probe {0} configured on OmniSwitch {1} / {2} failed").format(saa_name,ipadd,host)
            send_message(info,jid)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "SAA Name": saa_name}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
               print(error)
               pass 
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
    else:
        print("no pattern match - exiting script")
        sys.exit()
