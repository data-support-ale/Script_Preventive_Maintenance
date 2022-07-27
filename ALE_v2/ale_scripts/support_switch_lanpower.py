#!/usr/bin/env python3

from http.client import NOT_MODIFIED
import sys
import os
import json
import syslog
from time import strftime, localtime, sleep
from support_tools_OmniSwitch import get_credentials, collect_command_output_poe, ssh_connectivity_check
from support_send_notification import *
# from database_conf import *
import re
import time

from pattern import set_rule_pattern, set_portnumber, set_decision, get_decision, mysql_save

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

# Script init
script_name = sys.argv[0]
os.system('logger -t montag -p user.info Executing script ' + script_name)

pattern = sys.argv[1]
print(pattern)
set_rule_pattern(pattern)
# info = ("We received following pattern from RSyslog {0}").format(pattern)
# os.system('logger -t montag -p user.info ' + info)

# Get informations from logs.
switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company, room_id = get_credentials()

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
            if alelog.rsyslog_script_timeout(ipadd + port + pattern, time.time()):
                print("Less than 5 min")
                exit(0)
            
            # save_resp = check_save(ipadd, port, "lanpower")
            set_portnumber(port)
            decision = get_decision(ipadd)
            # if save_resp == "-1":
            if (len(decision) != 0) and ('No' in decision):
                print("Decision saved set to Never")
                sys.exit()
            else:
                pass
            filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status = collect_command_output_poe(switch_user, switch_password, host, ipadd, port, reason)
            send_file(filename_path, subject, action, result, category)
            set_decision(ipadd, "4")
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')
#            info = "Port {} from device {} has been detected in LANPOWER Fault state reason - {}".format(port, ipadd, reason)
#            send_message(info)
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
            if alelog.rsyslog_script_timeout(ipadd + port + pattern, time.time()):
                print("Less than 5 min")
                exit(0)

            # save_resp = check_save(ipadd, port, "lanpower")
            set_portnumber(port)
            set_decision(ipadd, "4")
            decision = get_decision(ipadd)
            # if save_resp == "-1":
            if (len(decision) != 0) and ('No' in decision):
                print("Decision saved set to Never")
                sys.exit()
            else:
                pass
            filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status = collect_command_output_poe(switch_user, switch_password, host, ipadd, port, reason)
            send_file(filename_path, subject, action, result, category)
            set_decision(ipadd, "4")
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')

#            info = "Port {} from device {} has been detected in LANPOWER Fault state reason - {}".format(port, ipadd, reason)
#            send_message(info)
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
            port, reason = re.findall(r"Port (.*?) FAULT State change 1b to 1e desc: Port is off: Underload state (.*)", msg)[0]
            if alelog.rsyslog_script_timeout(ipadd + port + pattern, time.time()):
                print("Less than 5 min")
                exit(0)
            print(port)
            print(reason)            
            # save_resp = check_save(ipadd, port, "lanpower")
            set_portnumber(port)
            decision = get_decision(ipadd)
            # if save_resp == "-1":
            if (len(decision) != 0) and ('No' in decision):
                print("Decision saved set to Never")
                sys.exit()
            else:
                pass
            filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status = collect_command_output_poe(switch_user, switch_password, host, ipadd, port, reason)
            send_file(filename_path, subject, action, result, category)
            set_decision(ipadd, "4")
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')

#            info = "Port {} from device {} has been detected in LANPOWER Fault state reason - {}".format(port, ipadd, reason)
#            send_message(info)
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
            if alelog.rsyslog_script_timeout(ipadd + port + pattern, time.time()):
                print("Less than 5 min")
                exit(0)
            
            # save_resp = check_save(ipadd, port, "lanpower")
            set_portnumber(port)
            decision = get_decision(ipadd)
            # if save_resp == "-1":
            if (len(decision) != 0) and ('No' in decision):
                print("Decision saved set to Never")
                sys.exit()
            else:
                pass
            filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status = collect_command_output_poe(switch_user, switch_password, host, ipadd, port, reason)
            send_file(filename_path, subject, action, result, category)
            set_decision(ipadd, "4")
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')

#            info = "Port {} from device {} has been detected in LANPOWER Fault state reason - {}".format(port, ipadd, reason)
#            send_message(info)
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()

    #Log sample
    # OS6860E_VC_Core swlogd lpNi LanNi INFO: Port 1 FAULT State change 1b to 43 desc: Port is off: Class Error (Illegal class)
    elif "FAULT State change 1b to 43" in msg:
        try:
            port, reason = re.findall(r"Port (.*?) FAULT State change 1b to 43 desc: Port is off: Class Error (.*)", msg)[0]
            if alelog.rsyslog_script_timeout(ipadd + port + pattern, time.time()):
                print("Less than 5 min")
                exit(0)
            
            # save_resp = check_save(ipadd, port, "lanpower")
            set_portnumber(port)
            decision = get_decision(ipadd)
            # if save_resp == "-1":
            if (len(decision) != 0) and ('No' in decision):
                print("Decision saved set to Never")
                sys.exit()
            else:
                pass
            filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status = collect_command_output_poe(switch_user, switch_password, host, ipadd, port, reason)
#            support_tools_OmniSwitch.send_file(filename_path, subject, action, result, category)
            send_file(filename_path, subject, action, result, category)
            set_decision(ipadd, "4")
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')

#            info = "Port {} from device {} has been detected in LANPOWER Fault state reason - {}".format(port, ipadd, reason)
#            send_message(info)
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()

    #Log sample
    # OS6465 swlogd lpNi LanNi INFO: Port 8 FAULT State change 11 to 35 desc: Port is off: Over temperature at the port (Port temperature protection mechanism was activated)
    elif "FAULT State change 11 to 35" in msg:
        try:
            port, reason = re.findall(r"Port (.*?) FAULT State change 11 to 35 desc: Port is off: Over temperature at the port (.*)", msg)[0]
            if alelog.rsyslog_script_timeout(ipadd + port + pattern, time.time()):
                print("Less than 5 min")
                exit(0)
            
            # save_resp = check_save(ipadd, port, "lanpower")
            set_portnumber(port)
            decision = get_decision(ipadd)
            # if save_resp == "-1":
            if (len(decision) != 0) and ('No' in decision):
                print("Decision saved set to Never")
                sys.exit()
            else:
                pass
            filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status = collect_command_output_poe(switch_user, switch_password, host, ipadd, port, reason)
#            support_tools_OmniSwitch.send_file(filename_path, subject, action, result, category)
            send_file(filename_path, subject, action, result, category)
            set_decision(ipadd, "4")
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')

#            info = "Port {} from device {} has been detected in LANPOWER Fault state reason - {}".format(port, ipadd, reason)
#            send_message(info)
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
    else:
        try:
            port, reason = re.findall(r"Port (.*?) FAULT State change 11 to 35 desc: Port is off: Over temperature at the port (.*)", msg)[0]
            if alelog.rsyslog_script_timeout(ipadd + port + pattern, time.time()):
                print("Less than 5 min")
                exit(0)
            port, state_a, state_b, reason = re.findall(r"Port (.*?) FAULT State change (.*?) to (.*?) desc: (.*)", msg)[0]
            os.system('logger -t montag -p user.info Port ' + port)
            os.system('logger -t montag -p user.info State A ' + state_a)
            os.system('logger -t montag -p user.info State B ' + state_b)
            print(reason)
            #os.system('logger -t montag -p user.info Reason ' + reason)
            if alelog.rsyslog_script_timeout(ipadd + port + pattern, time.time()):
                print("Less than 5 min")
                exit(0)
            
            # save_resp = check_save(ipadd, port, "lanpower")
            set_portnumber(port)
            decision = get_decision(ipadd)
            # if save_resp == "-1":
            if (len(decision) != 0) and ('No' in decision):
                print("Decision saved set to Never")
                sys.exit()
            else:
                pass
            filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status = collect_command_output_poe(switch_user, switch_password, host, ipadd, port, reason)
#            support_tools_OmniSwitch.send_file(filename_path, subject, action, result, category)
            send_file(filename_path, subject, action, result, category)
            set_decision(ipadd, "4")
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')

#            info = "Port {} from device {} has been detected in LANPOWER Fault state reason - {}".format(port, ipadd, reason)
#            send_message(info)
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()

# always 1
#never -1
# ? 0
decision = get_decision(ipadd)

# if save_resp == "0":
if (len(decision) == 0) or (len(decision) == 1 and decision[0] == 'Yes'):
    if capacitor_detection_status == "enabled" or high_resistance_detection_status == "enabled" or reason == "(Illegal class)":
        if capacitor_detection_status == "enabled":
            feature = "Disable Capacitor-Detection"
        elif high_resistance_detection_status == "enabled":
            feature = "Disable High-Resistance-Detection"
        elif reason == "(Illegal class)":
            feature = "Disable 4Pair"

        notif = ("A LANPOWER issue is detected on OmniSwitch {0} / {1} Port: 1/1/{2} \
           , reason: {3}.\nDo you want to disable PoE on this port? " + ip_server).format(host,ipadd,port,reason,ip_server)
        # answer = send_message_request_advanced(notif, jid,feature)
        answer = send_message_request_advanced(notif, feature)
        print(answer)
        set_decision(ipadd, answer)
             
    else:
        feature = "Reload PoE on port"
        notif = ("A LANPOWER issue is detected on OmniSwitch {0} / {1} Port: 1/1/{2} \
            , reason: {3}.\nDo you want to disable PoE on this port? " + ip_server).format(host,ipadd,port,reason,ip_server)
        # answer = send_message_request_advanced(notif, jid, feature)
        answer = send_message_request_advanced(notif, feature)
        print(answer)
        set_decision(ipadd, answer)

# elif save_resp == "-1":
elif 'No' in decision:
    try:
        print(port)
        print(reason)
        print(ipadd)      
        sys.exit()   
    except UnboundLocalError as error:
       print(error)
       sys.exit()
    except Exception as error:
        print(error)
        sys.exit() 

# elif save_resp == "1":
elif 'yes and remember' in [d.lower() for d in decision]:
    answer = '2'
else:
    answer = '1'

if answer == '1':
    os.system('logger -t montag -p user.info Process terminated')
    # DISABLE PoE on Port
    cmd = "lanpower port 1/1/" + port + " admin-state disable"
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
    os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user, ipadd, cmd))
     
    info = "PoE is administratively disabled on port 1/1/{} of OmniSwitch: {}/{}".format(port,host,ipadd)
    syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
    send_message(notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
    set_decision(ipadd, "4")
    try:
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
        syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision")    
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass   

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
        
        send_message(info)
        set_decision(ipadd, "3")
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=info, exception='')

    elif high_resistance_detection_status == "enabled":
        cmd = "lanpower slot 1/1 high-resistance-detection disable"
        info = "High-Resistance-Detection is administratively disabled on slot 1/1 of OmniSwitch: {}/{}".format(host,ipadd)
        ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
        
        send_message(info)
        set_decision(ipadd, "3")
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=info, exception='')

    elif reason == "(Illegal class)":
        cmd = "lanpower port 1/1/" + port + " 4pair disable"
        info = "4Pair is disabled on port 1/1/{} of OmniSwitch: {}/{}".format(port,host,ipadd)
        ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
             
        send_message(info)
        set_decision(ipadd, "3")
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=info, exception='')
           
    ### else it corresponds to PoE Reload
    else:
        l_switch_cmd = []
        l_switch_cmd.append("lanpower port 1/1/" + port + " admin-state disable")
        l_switch_cmd.append("sleep 2")
        l_switch_cmd.append("lanpower port 1/1/" + port + " admin-state enable")
        for switch_cmd in l_switch_cmd:
            ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
        info = "PoE is reloaded on port 1/1/{} of OmniSwitch: {}/{}".format(port,host,ipadd)
                
        send_message(info)
        set_decision(ipadd, "3")
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=info, exception='')

#    os.system("sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user, ipadd, cmd))

else:
    print("Mail request set as no")
    os.system('logger -t montag -p user.info Mail request set as no')
    sleep(1)
