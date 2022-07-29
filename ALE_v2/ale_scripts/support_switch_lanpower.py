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
import syslog

syslog.openlog('support_switch_lanpower')
syslog.syslog(syslog.LOG_INFO, "Executing script")

from pattern import set_rule_pattern, set_portnumber, set_decision, get_decision, mysql_save

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
_runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

path = os.path.dirname(__file__)
print(os.path.abspath(os.path.join(path,os.pardir)))
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

# Script init
script_name = sys.argv[0]

pattern = sys.argv[1]
print(pattern)
set_rule_pattern(pattern)

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
        print(msg)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog IP Address: " + ipadd)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog Hostname: " + host)
        #syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + msg)
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_lanpower.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_lanpower.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_lanpower.json - Index error in regex")
        exit()

    # Sample log
    # OS6860E swlogd lpNi LanNi INFO: Port 46 FAULT State change 1b to 24 desc: Port is off: Voltage injection into the port (Port fails due to voltage being applied to the port from external source)
    if "FAULT State change 1b to 24" in msg:
        try:
            pattern = "FAULT state change 1b to 24"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            port, reason = re.findall(r"Port (.*?) FAULT State change 1b to 24 desc: Port is off: Voltage injection into the port (.*)", msg)[0]
            syslog.syslog(syslog.LOG_INFO, "LANPOWER fault noticed on port " + port + " reason " + reason)
            if alelog.rsyslog_script_timeout(ipadd + port + pattern, time.time()):
                print("Less than 5 min")
                syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
                exit(0)
            
            set_portnumber(port)
            decision = get_decision(ipadd)
            if (len(decision) != 0) and ('No' in decision):
                print("Decision saved set to Never")
                syslog.syslog(syslog.LOG_INFO, "Decision saved set to Never - script exit")
                sys.exit()
            else:
                pass
            syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_poe")
            filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status = collect_command_output_poe(switch_user, switch_password, host, ipadd, port, reason)
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")    
            send_file(filename_path, subject, action, result, category)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            set_decision(ipadd, "4")
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
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
            pattern = "FAULT state change 1b to 25"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            port, reason = re.findall(r"Port (.*?) FAULT State change 1b to 25 desc: Port is off: Improper Capacitor Detection results or Detection values indicating short \((.*) or Fail due to detec", msg)[0]
            syslog.syslog(syslog.LOG_INFO, "LANPOWER fault noticed on port " + port + " reason " + reason)
            if alelog.rsyslog_script_timeout(ipadd + port + pattern, time.time()):
                print("Less than 5 min")
                syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
                exit(0)

            set_portnumber(port)
            decision = get_decision(ipadd)
            if (len(decision) != 0) and ('No' in decision):
                print("Decision saved set to Never")
                syslog.syslog(syslog.LOG_INFO, "Decision saved set to Never - script exit")
                sys.exit()
            else:
                pass
            syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_poe")
            filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status = collect_command_output_poe(switch_user, switch_password, host, ipadd, port, reason)
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")    
            send_file(filename_path, subject, action, result, category)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            set_decision(ipadd, "4")
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
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
            pattern = "FAULT state change 1b to 1e"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            port, reason = re.findall(r"Port (.*?) FAULT State change 1b to 1e desc: Port is off: Underload state (.*)", msg)[0]
            syslog.syslog(syslog.LOG_INFO, "LANPOWER fault noticed on port " + port + " reason " + reason)
            if alelog.rsyslog_script_timeout(ipadd + port + pattern, time.time()):
                print("Less than 5 min")
                syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
                exit(0)

            set_portnumber(port)
            decision = get_decision(ipadd)
            if (len(decision) != 0) and ('No' in decision):
                print("Decision saved set to Never")
                syslog.syslog(syslog.LOG_INFO, "Decision saved set to Never - script exit")
                sys.exit()
            else:
                pass
            syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_poe")
            filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status = collect_command_output_poe(switch_user, switch_password, host, ipadd, port, reason)
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")    
            send_file(filename_path, subject, action, result, category)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            set_decision(ipadd, "4")
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
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
            pattern = "FAULT state change 1b to 1c"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            port, reason = re.findall(r"Port (.*?) FAULT State change 1b to 1c desc: Port is off: Non-802.3AF/AT powered device ((.*?))", msg)[0]
            syslog.syslog(syslog.LOG_INFO, "LANPOWER fault noticed on port " + port + " reason " + reason)
            if alelog.rsyslog_script_timeout(ipadd + port + pattern, time.time()):
                print("Less than 5 min")
                syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
                exit(0)

            set_portnumber(port)
            decision = get_decision(ipadd)
            if (len(decision) != 0) and ('No' in decision):
                print("Decision saved set to Never")
                syslog.syslog(syslog.LOG_INFO, "Decision saved set to Never - script exit")
                sys.exit()
            else:
                pass
            syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_poe")
            filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status = collect_command_output_poe(switch_user, switch_password, host, ipadd, port, reason)
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")    
            send_file(filename_path, subject, action, result, category)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            set_decision(ipadd, "4")
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
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
            pattern = "FAULT State change 1b to 43"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            port, reason = re.findall(r"Port (.*?) FAULT State change 1b to 43 desc: Port is off: Class Error (.*)", msg)[0]
            syslog.syslog(syslog.LOG_INFO, "LANPOWER fault noticed on port " + port + " reason " + reason)
            if alelog.rsyslog_script_timeout(ipadd + port + pattern, time.time()):
                print("Less than 5 min")
                syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
                exit(0)

            set_portnumber(port)
            decision = get_decision(ipadd)
            if (len(decision) != 0) and ('No' in decision):
                print("Decision saved set to Never")
                syslog.syslog(syslog.LOG_INFO, "Decision saved set to Never - script exit")
                sys.exit()
            else:
                pass
            syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_poe")
            filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status = collect_command_output_poe(switch_user, switch_password, host, ipadd, port, reason)
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")    
            send_file(filename_path, subject, action, result, category)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            set_decision(ipadd, "4")
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
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
            pattern = "FAULT State change 11 to 35"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            port, reason = re.findall(r"Port (.*?) FAULT State change 11 to 35 desc: Port is off: Over temperature at the port (.*)", msg)[0]
            syslog.syslog(syslog.LOG_INFO, "LANPOWER fault noticed on port " + port + " reason " + reason)
            if alelog.rsyslog_script_timeout(ipadd + port + pattern, time.time()):
                print("Less than 5 min")
                syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
                exit(0)

            set_portnumber(port)
            decision = get_decision(ipadd)
            if (len(decision) != 0) and ('No' in decision):
                print("Decision saved set to Never")
                syslog.syslog(syslog.LOG_INFO, "Decision saved set to Never - script exit")
                sys.exit()
            else:
                pass
            syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_poe")
            filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status = collect_command_output_poe(switch_user, switch_password, host, ipadd, port, reason)
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")    
            send_file(filename_path, subject, action, result, category)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            set_decision(ipadd, "4")
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
    else:
        try:
            syslog.syslog(syslog.LOG_INFO, "No pattern matching")
            port, state_a, state_b, reason = re.findall(r"Port (.*?) FAULT State change (.*?) to (.*?) desc: (.*)", msg)[0]
            if alelog.rsyslog_script_timeout(ipadd + port + pattern, time.time()):
                print("Less than 5 min")
                syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
                exit(0)
            
            set_portnumber(port)
            decision = get_decision(ipadd)
            if (len(decision) != 0) and ('No' in decision):
                print("Decision saved set to Never")
                syslog.syslog(syslog.LOG_INFO, "Decision saved set to Never - script exit")
                sys.exit()
            else:
                pass
            syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_poe")
            filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status = collect_command_output_poe(switch_user, switch_password, host, ipadd, port, reason)
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")            
            send_file(filename_path, subject, action, result, category)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            set_decision(ipadd, "4")
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=action, exception='')
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()

syslog.syslog(syslog.LOG_INFO, "Executing function get_decision")
decision = get_decision(ipadd)

# if save_resp == "0":
if (len(decision) == 0) or (len(decision) == 1 and decision[0] == 'Yes'):
    syslog.syslog(syslog.LOG_INFO, "No Decision saved")
    if capacitor_detection_status == "enabled" or high_resistance_detection_status == "enabled" or reason == "(Illegal class)":
        if capacitor_detection_status == "enabled":
            syslog.syslog(syslog.LOG_INFO, "capacitor_detection is enabled")
            feature = "Disable Capacitor-Detection"
        elif high_resistance_detection_status == "enabled":
            syslog.syslog(syslog.LOG_INFO, "High-Resistance-Detection is enabled")
            feature = "Disable High-Resistance-Detection"
        elif reason == "(Illegal class)":
            syslog.syslog(syslog.LOG_INFO, "Reason is Illegal Class")
            feature = "Disable 4Pair"
        notif = ("A LANPOWER issue is detected on OmniSwitch {0} / {1} Port: 1/1/{2} , reason: {3}.\nDo you want to disable PoE on this port? " + ip_server).format(host,ipadd,port,reason,ip_server)
        syslog.syslog(syslog.LOG_INFO, notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card Advanced with 4th option: " + feature)
        answer = send_message_request_advanced(notif, feature)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

        print(answer)
        syslog.syslog(syslog.LOG_INFO, "Executing function set_decision: " + answer)
        set_decision(ipadd, answer)
        try:
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif + " Decision received: " + answer, exception='')
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")    
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass               
    else:
        feature = "Reload PoE on port"
        notif = ("A LANPOWER issue is detected on OmniSwitch {0} / {1} Port: 1/1/{2} \
        , reason: {3}.\nDo you want to disable PoE on this port? " + ip_server).format(host,ipadd,port,reason,ip_server)
        syslog.syslog(syslog.LOG_INFO, notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card Advanced with 4th option: " + feature)
        answer = send_message_request_advanced(notif, feature)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        print(answer)
        syslog.syslog(syslog.LOG_INFO, "Executing function set_decision: " + answer)
        set_decision(ipadd, answer)
        try:
            mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif + " Decision received: " + answer, exception='')
            syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision")    
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass   
# elif save_resp == "-1":
elif 'No' in decision:
    print("Decision saved to No - script exit")
    syslog.syslog(syslog.LOG_INFO, "Decision saved to No - script exit") 
    sys.exit()   

# elif save_resp == "1":
elif 'yes and remember' in [d.lower() for d in decision]:
    answer = '2'
    print("Decision saved to Yes and remember")
    syslog.syslog(syslog.LOG_INFO, "Decision saved to Yes and remember")
else:
    answer = '1'
    syslog.syslog(syslog.LOG_INFO, "No answer - Decision set to Yes - Script exit - will be called by next occurence")    

syslog.syslog(syslog.LOG_INFO, "Rainbow Acaptive Card answer: " + answer)

if answer == '1':
    syslog.syslog(syslog.LOG_INFO, "Decision set to Yes - We disable the PoE on port")
    # DISABLE PoE on Port
    cmd = "lanpower port 1/1/" + port + " admin-state disable"
    syslog.syslog(syslog.LOG_INFO, "SSH Session start")
    syslog.syslog(syslog.LOG_INFO, "Command executed: " + cmd)    
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
    syslog.syslog(syslog.LOG_INFO, "SSH Session end")

    notif = "Preventive Maintenance Application - PoE is administratively disabled on port 1/1/{} of OmniSwitch: {}/{}".format(port,host,ipadd)
    syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
    send_message(notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
    set_decision(ipadd, "4")
    try:
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif + " Decision set to Yes", exception='')
        syslog.syslog(syslog.LOG_INFO, "Statistics saved")    
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass   

elif answer == '2':
    syslog.syslog(syslog.LOG_INFO, "Decision is Yes and Remember - PoE is administratively disabled on port")
    # DISABLE PoE on Port
    cmd = "lanpower port 1/1/" + port + " admin-state disable"
    syslog.syslog(syslog.LOG_INFO, "SSH Session start")
    syslog.syslog(syslog.LOG_INFO, "Command executed: " + cmd) 
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
    syslog.syslog(syslog.LOG_INFO, "SSH Session end")
    set_decision(ipadd, "4")
    try:
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif + " Decision set to Yes and Remember", exception='')
        syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision")    
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 

## Value 3 when we return advanced value like Capacitor Detection or High Resistance Capacity
elif answer == '3':
    # DISABLE PoE on Port
    if capacitor_detection_status == "enabled":
        syslog.syslog(syslog.LOG_INFO, "Capacitor Detection is enabled and received answer 3")
        cmd = "lanpower slot 1/1 capacitor-detection disable"
        syslog.syslog(syslog.LOG_INFO, "SSH Session start")
        syslog.syslog(syslog.LOG_INFO, "Command executed: " + cmd) 
        ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
        syslog.syslog(syslog.LOG_INFO, "SSH Session end")
        notif = "Capacitor-Detection is administratively disabled on slot 1/1 of OmniSwitch: {}/{}".format(host,ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Sending notification")
        send_message(notif)
        set_decision(ipadd, "4")
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
        syslog.syslog(syslog.LOG_INFO, "Statistics saved")  
    elif high_resistance_detection_status == "enabled":
        syslog.syslog(syslog.LOG_INFO, "High Resistance Detection is enabled and received answer 3")
        cmd = "lanpower slot 1/1 high-resistance-detection disable"
        syslog.syslog(syslog.LOG_INFO, "SSH Session start")
        syslog.syslog(syslog.LOG_INFO, "Command executed: " + cmd) 
        ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
        syslog.syslog(syslog.LOG_INFO, "SSH Session end")
        notif = "High-Resistance-Detection is administratively disabled on slot 1/1 of OmniSwitch: {}/{}".format(host,ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Sending notification")
        send_message(notif)
        set_decision(ipadd, "4")
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
        syslog.syslog(syslog.LOG_INFO, "Statistics saved")  
    elif reason == "(Illegal class)":
        syslog.syslog(syslog.LOG_INFO, "Illegal class and received answer 3")
        cmd = "lanpower port 1/1/" + port + " 4pair disable"
        syslog.syslog(syslog.LOG_INFO, "SSH Session start")
        syslog.syslog(syslog.LOG_INFO, "Command executed: " + cmd) 
        ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
        syslog.syslog(syslog.LOG_INFO, "SSH Session end")
        notif = "4Pair is disabled on port 1/1/{} of OmniSwitch: {}/{}".format(port,host,ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Sending notification")
        send_message(notif)
        set_decision(ipadd, "4")
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
        syslog.syslog(syslog.LOG_INFO, "Statistics saved")             
    ### else it corresponds to PoE Reload
    else:
        syslog.syslog(syslog.LOG_INFO, "PoE Reload received answer 3")
        l_switch_cmd = []
        l_switch_cmd.append(("lanpower port 1/1/{0} admin-state disable; sleep 2; lanpower port 1/1/{0} admin-state enable").format(port))
        for switch_cmd in l_switch_cmd:
            syslog.syslog(syslog.LOG_INFO, "SSH Session start")
            syslog.syslog(syslog.LOG_INFO, "Command executed: " + switch_cmd) 
            ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
            syslog.syslog(syslog.LOG_INFO, "SSH Session end")
        notif = "PoE is reloaded on port 1/1/{} of OmniSwitch: {}/{}".format(port,host,ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
        send_message(notif)
        set_decision(ipadd, "4")
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif, exception='')
        syslog.syslog(syslog.LOG_INFO, "Statistics saved")       

else:
    print("No decision matching - script exit")
    syslog.syslog(syslog.LOG_INFO, "No decision matching - script exit")
    sleep(1)
    sys.exit()
