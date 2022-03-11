#!/usr/local/bin/python3.7

import sys
import os
import json
from time import strftime, localtime, sleep
from support_tools_OmniSwitch import get_credentials, send_file, collect_command_output_poe, check_save, add_new_save, ssh_connectivity_check
from support_send_notification import send_message, send_message_request, send_message_request_advanced
from database_conf import *
import re

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

last = ""
with open("/var/log/devices/lastlog_lanpower.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_lanpower.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_lanpower.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_lanpower.json empty")
        exit()
    except IndexError:
        print("Index error in regex")
        exit()

    # Sample log
    # OS6860E swlogd lpNi LanNi INFO: Port 46 FAULT State change 1b to 24 desc: Port is off: Voltage injection into the port (Port fails due to voltage being applied to the port from external source)
    if "FAULT State change 1b to 24" in msg:
        try:
            port, reason = re.findall(r"Port (.*?) FAULT State change 1b to 24 desc: Port is off: Voltage injection into the port (.*)", msg)[0]
            save_resp = check_save(ipadd, port, "lanpower")
            if save_resp == "-1":
                print("Decision saved set to Never")
                sys.exit()
            else:
                pass
            filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status = collect_command_output_poe(switch_user, switch_password, host, ipadd, port, reason)
            send_file(filename_path, subject, action, result, category)
#            info = "Port {} from device {} has been detected in LANPOWER Fault state reason - {}".format(port, ipadd, reason)
#            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "Port": port, "Reason": reason}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
    # Sample log
    # OS6860E swlogd lpNi LanNi INFO: Port 15 FAULT State change 1b to 25 desc: Port is off: Improper Capacitor Detection results or Detection values indicating short (Fail due to out-of-range capacitor value or Fail due to detected short
    elif "FAULT State change 1b to 25" in msg:
        try:
            port, reason = re.findall(r"Port (.*?) FAULT State change 1b to 25 desc: Port is off: Improper Capacitor Detection results or Detection values indicating short \((.*) or Fail due to detec", msg)[0]
            save_resp = check_save(ipadd, port, "lanpower")
            if save_resp == "-1":
                print("Decision saved set to Never")
                sys.exit()
            else:
                pass
            filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status = collect_command_output_poe(switch_user, switch_password, host, ipadd, port, reason)
            send_file(filename_path, subject, action, result, category)
#            info = "Port {} from device {} has been detected in LANPOWER Fault state reason - {}".format(port, ipadd, reason)
#            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "Port": port, "Reason": reason}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
    # Sample log
    # OS6860E swlogd lpNi LanNi INFO: Port 46 FAULT State change 1b to 1e desc: Port is off: Underload state (Underload state according to 802.3AF\/AT, current is below Imin)
    elif "FAULT State change 1b to 1e" in msg:
        try:
            port, reason = re.findall(r"Port (.*?) FAULT State change 1b to 1e desc: Port is off: Underload state ((.*?))", msg)[0]
            save_resp = check_save(ipadd, port, "lanpower")
            if save_resp == "-1":
                print("Decision saved set to Never")
                sys.exit()
            else:
                pass
            filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status = collect_command_output_poe(switch_user, switch_password, host, ipadd, port, reason)
            send_file(filename_path, subject, action, result, category)
#            info = "Port {} from device {} has been detected in LANPOWER Fault state reason - {}".format(port, ipadd, reason)
#            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "Port": port, "Reason": reason}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
    # Sample log
    # OS6860E swlogd lpNi LanNi INFO: Port 44 FAULT State change 1b to 1c desc: Port is off: Non-802.3AF/AT powered device (Non-standard PD connected)
    elif "FAULT State change 1b to 1c" in msg:
        try:
            port, reason = re.findall(r"Port (.*?) FAULT State change 1b to 1c desc: Port is off: Non-802.3AF/AT powered device ((.*?))", msg)[0]
            save_resp = check_save(ipadd, port, "lanpower")
            if save_resp == "-1":
                print("Decision saved set to Never")
                sys.exit()
            else:
                pass
            filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status = collect_command_output_poe(switch_user, switch_password, host, ipadd, port, reason)
            send_file(filename_path, subject, action, result, category)
#            info = "Port {} from device {} has been detected in LANPOWER Fault state reason - {}".format(port, ipadd, reason)
#            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "Port": port, "Reason": reason}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
    else:
        print("no pattern match - exiting script")
        sys.exit()

# always 1
#never -1
# ? 0
save_resp = check_save(ipadd, port, "lanpower")

if save_resp == "0":
        if capacitor_detection_status == "enabled" or high_resistance_detection_status == "enabled":
            if capacitor_detection_status == "enabled":
               feature = "Disable Capacitor-Detection"
            elif high_resistance_detection_status == "enabled":
                feature = "Disable High-Resistance-Detection"
            notif = "A LANPOWER issue is detected on OmniSwitch " + host + " Port: 1/1/" + port + \
            ", reason: " + reason + ". Do you want to disable PoE on this port? " + ip_server
            answer = send_message_request_advanced(notif, jid,feature)
            print(answer)
            if answer == "2":
                add_new_save(ipadd, port, "lanpower", choice="always")
            elif answer == "0":
                add_new_save(ipadd, port, "lanpower", choice="never")       
        else:
            notif = "A LANPOWER issue is detected on OmniSwitch " + host + " Port: 1/1/" + port + \
            ", reason: " + reason + ". Do you want to disable PoE on this port? " + ip_server
            answer = send_message_request(notif, jid)
            print(answer)
            if answer == "2":
                add_new_save(ipadd, port, "lanpower", choice="always")
            elif answer == "0":
                add_new_save(ipadd, port, "lanpower", choice="never")

elif save_resp == "-1":
    try:
        print(port)
        print(reason)
        print(ipadd)
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "Port": port, "Reason": reason}, "fields": {"count": 1}}])        
        sys.exit()   
    except UnboundLocalError as error:
       print(error)
       sys.exit()

elif save_resp == "1":
    answer = '2'
else:
    answer = '1'

if answer == '1':
    os.system('logger -t montag -p user.info Process terminated')
    # DISABLE PoE on Port
    cmd = "lanpower port 1/1/" + port + " admin-state disable"
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
    os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user, ipadd, cmd))
     
    if jid != '':
        info = "PoE is administratively disabled on port 1/1/{} of OmniSwitch: {}/{}".format(port,host,ipadd)
        send_message(info, jid)

elif answer == '2':
    os.system('logger -t montag -p user.info Process terminated')
    # DISABLE PoE on Port
    cmd = "lanpower port 1/1/" + port + " admin-state disable"
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
#    os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user, ipadd, cmd))

## Value 3 when we return advanced value like Capacitor Detection or High Resistance Capacity
elif answer == '3':
    os.system('logger -t montag -p user.info Process terminated')
    # DISABLE PoE on Port
    if capacitor_detection_status == "enabled":
        cmd = "lanpower slot 1/1 capacitor-detection disable"
        ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
        info = "Capacitor-Detection is administratively disabled on slot 1/1 of OmniSwitch: {}/{}".format(host,ipadd)
        send_message(info, jid)
    elif high_resistance_detection_status == "enabled":
        cmd = "lanpower slot 1/1 high-resistance-detection disable"
        info = "High-Resistance-Detection is administratively disabled on slot 1/1 of OmniSwitch: {}/{}".format(host,ipadd)
        ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
        send_message(info, jid)
#    os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user, ipadd, cmd))


else:
    print("Mail request set as no")
    os.system('logger -t montag -p user.info Mail request set as no')
    sleep(1)

try:
    write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "Port": port, "Reason": reason}, "fields": {"count": 1}}])
except UnboundLocalError as error:
    print(error)
    sys.exit()