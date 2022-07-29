#!/usr/bin/env python3

import sys
import os
import json
from time import strftime, localtime
from support_tools_OmniSwitch import get_credentials, collect_command_output_ovc, ssh_connectivity_check
from support_send_notification import *
from database_conf import *
import re
import time
import syslog

syslog.openlog('support_switch_ovcirrus')
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

switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company = get_credentials()

last = ""
with open("/var/log/devices/lastlog_ovc.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_ovc.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_ovc.json", "r", errors='ignore') as log_file:
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
        print("File /var/log/devices/lastlog_ovc.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_ovc.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_ovc.json - Index error in regex")
        exit()


    # Sample log
    # OS6860E swlogd OPENVPN(168) Data: TCP: connect to [AF_INET]18.194.174.46:443 failed: S_errno_EHOSTUNREACH
    if "S_errno_EHOSTUNREACH" in msg:
        pattern = "S_errno_EHOSTUNREACH"
        syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
        syslog.syslog(syslog.LOG_INFO, "Executing function set_portnumber 0")
        set_portnumber("0")
        if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
            print("Less than 5 min")
            syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
            exit(0)

        syslog.syslog(syslog.LOG_INFO, "Executing function get_decision")
        decision = get_decision(ipadd)
        if (len(decision) != 0) and ('No' in decision):
            print("Decision saved set to Never")
            syslog.syslog(syslog.LOG_INFO, "Decision saved set to Never - script exit")
            sys.exit()
        else:
            pass

        try:
            vpn_ip, reason = re.findall(r"\[AF_INET\](.*?):443 failed: (.*)", msg)[0]
            print(vpn_ip)
            print(reason)
            filename_path, subject, action, result, category = collect_command_output_ovc(switch_user, switch_password, vpn_ip, reason, host, ipadd)
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
    # OS6860E swlogd OPENVPN(168) Data: TCP: connect to [AF_INET]18.194.174.46:443 failed: S_errno_ETIMEDOUT
    elif "S_errno_ETIMEDOUT" in msg:
        pattern = "S_errno_ETIMEDOUT"
        syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
        syslog.syslog(syslog.LOG_INFO, "Executing function set_portnumber 0")
        set_portnumber("0")
        if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
            print("Less than 5 min")
            syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
            exit(0)

        syslog.syslog(syslog.LOG_INFO, "Executing function get_decision")
        decision = get_decision(ipadd)
        if (len(decision) != 0) and ('No' in decision):
            print("Decision saved set to Never")
            syslog.syslog(syslog.LOG_INFO, "Decision saved set to Never - script exit")
            sys.exit()
        else:
            pass
        try:
            vpn_ip, reason = re.findall(r"[AF_INET](.*?):443 failed: (.*)", msg)[0]
            filename_path, subject, action, result, category = collect_command_output_ovc(switch_user, switch_password, vpn_ip, reason, host, ipadd)
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
    # OS6860E swlogd openvpn[17911] RESOLVE: Cannot resolve host address: psza60a0ivu6v2.tenant.vpn.myovcloud.com:443 (Temporary failure in name resolution)
    elif "Cannot resolve host address" in msg:
        pattern = "Cannot resolve host address"
        syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
        syslog.syslog(syslog.LOG_INFO, "Executing function set_portnumber 0")
        set_portnumber("0")
        if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
            print("Less than 5 min")
            syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
            exit(0)

        syslog.syslog(syslog.LOG_INFO, "Executing function get_decision")
        decision = get_decision(ipadd)
        if (len(decision) != 0) and ('No' in decision):
            print("Decision saved set to Never")
            syslog.syslog(syslog.LOG_INFO, "Decision saved set to Never - script exit")
            sys.exit()
        else:
            pass
        try:
            vpn_ip= re.findall(r"Cannot resolve host address: (.*?):443", msg)[0]
            reason = "Cannot resolve host address"
            filename_path, subject, action, result, category = collect_command_output_ovc(switch_user, switch_password, vpn_ip, reason, host, ipadd)
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
    # OS6860E swlogd ovcCmm OVCloud ERR: ovcProcessCallHomeResponseSuccess: Invalid process status
    elif "Invalid process status" in msg:
        pattern = "Invalid process status"
        syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
        syslog.syslog(syslog.LOG_INFO, "Executing function set_portnumber 0")
        set_portnumber("0")
        if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
            print("Less than 5 min")
            syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
            exit(0)

        syslog.syslog(syslog.LOG_INFO, "Executing function get_decision")
        decision = get_decision(ipadd)
        if (len(decision) != 0) and ('No' in decision):
            print("Decision saved set to Never")
            syslog.syslog(syslog.LOG_INFO, "Decision saved set to Never - script exit")
            sys.exit()
        else:
            pass

        try:
            reason = "Invalid process status"
            vpn_ip = "0"
            filename_path, subject, action, result, category = collect_command_output_ovc(switch_user, switch_password, vpn_ip, reason, host, ipadd)
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
    # OS6860E OPENVPN(168) Data: Fatal TLS error (check_tls_errors_co), restarting
    elif "Fatal TLS error" in msg:
        pattern = "Fatal TLS error"
        syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
        syslog.syslog(syslog.LOG_INFO, "Executing function set_portnumber 0")
        set_portnumber("0")
        if alelog.rsyslog_script_timeout(ipadd + "0" + pattern, time.time()):
            print("Less than 5 min")
            syslog.syslog(syslog.LOG_INFO, "Script executed within 5 minutes interval - script exit")
            exit(0)

        syslog.syslog(syslog.LOG_INFO, "Executing function get_decision")
        decision = get_decision(ipadd)
        if (len(decision) != 0) and ('No' in decision):
            print("Decision saved set to Never")
            syslog.syslog(syslog.LOG_INFO, "Decision saved set to Never - script exit")
            sys.exit()
        else:
            pass

        try:
            reason = "Fatal TLS error"
            vpn_ip = "0"
            notif = "Preventive Maintenance Application - A Fatal TLS error has been detected on OmniSwitch (IP : {0} / {1}) syslogs on the OPENVPN task.\nPlease check the certificate status (must be Consistent).\nAs a workaround you can restart the cloud-agent (cloud-agent admin-state restart).".format(ipadd, host)
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
            send_message(notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            filename_path, subject, action, result, category = collect_command_output_ovc(switch_user, switch_password, vpn_ip, reason, host, ipadd)
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
        print("no pattern match - exiting script")
        syslog.syslog(syslog.LOG_INFO, "No pattern match - exiting script")
        sys.exit()

syslog.syslog(syslog.LOG_INFO, "Executing function get_decision")
decision = get_decision(ipadd)

if (len(decision) == 0) or (len(decision) == 1 and decision[0] == 'Yes'):
        syslog.syslog(syslog.LOG_INFO, "No Decision saved")
        if reason == "S_errno_EHOSTUNREACH" or reason == "S_errno_ETIMEDOUT":
            feature = "Restart Cloud-Agent"
            notif = "An OpenVPN issue is detected on OmniSwitch " + host + " reason: " + reason + ".\nDo you want to disable the Cloud-Agent on this switch? This command will result in device being disconnected from OV in cloud." + ip_server
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Rainbow Adaptive Card of type Advanced")
            answer = send_message_request_advanced(notif, feature)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            syslog.syslog(syslog.LOG_INFO, "Rainbow Adaptive Card Answer: " + answer)
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
        else:
            feature = "Restart Cloud-Agent"
            notif = "A Cloud-Agent issue is detected on OmniSwitch " + host + " reason: " + reason + ".\nDo you want to disable the Cloud-Agent on this switch? This command will result in device being disconnected from OV in cloud. " + ip_server
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Rainbow Adaptive Card of type Advanced")
            answer = send_message_request_advanced(notif, feature)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            syslog.syslog(syslog.LOG_INFO, "Rainbow Adaptive Card Answer: " + answer)
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
    syslog.syslog(syslog.LOG_INFO, "Decision set to Yes - cloud-agent is disabled")
    # DISABLE Cloud-agent
    l_switch_cmd = []
    l_switch_cmd.append("cloud-agent admin-state disable")
    for switch_cmd in l_switch_cmd:
        syslog.syslog(syslog.LOG_INFO, "SSH Session start")
        syslog.syslog(syslog.LOG_INFO, "Command executed: " + switch_cmd)
        ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
        syslog.syslog(syslog.LOG_INFO, "SSH Session end")
    notif = "Cloud-Agent service is stopped on OmniSwitch: {}/{}".format(host,ipadd)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
    answer = send_message(notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")       
    set_decision(ipadd, "4")
    try:
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif + " Decision set to Yes", exception='')
        syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision")    
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass  
elif answer == '2':
    syslog.syslog(syslog.LOG_INFO, "Decision is Yes and Remember - cloud-agent admin-state disable")
    # DISABLE Cloud-agent
    l_switch_cmd = []
    l_switch_cmd.append("cloud-agent admin-state disable")
    for switch_cmd in l_switch_cmd:
        syslog.syslog(syslog.LOG_INFO, "SSH Session start")
        syslog.syslog(syslog.LOG_INFO, "Command executed: " + switch_cmd)
        ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
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
## Value 3 when we return advanced value we reload the Cloud-Agent
elif answer == '3':
    syslog.syslog(syslog.LOG_INFO, "Decision is Yes and Remember - cloud-agent is reloaded")
    # Cloud-agent restart
    cmd = "cloud-agent admin-state restart"
    syslog.syslog(syslog.LOG_INFO, "SSH Session start")
    syslog.syslog(syslog.LOG_INFO, "Command executed: " + cmd)
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
    syslog.syslog(syslog.LOG_INFO, "SSH Session end")
    notif = "Cloud-Agent is restarted on OmniSwitch: {}/{}".format(host,ipadd)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
    answer = send_message(notif)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent") 
    set_decision(ipadd, "4")
    try:
        mysql_save(runtime=_runtime, ip_address=ipadd, result='success', reason=notif + " Decision set to Reload Cloud-Agent", exception='')
        syslog.syslog(syslog.LOG_INFO, "Statistics saved with no decision")    
    except UnboundLocalError as error:
        print(error)
        sys.exit()
    except Exception as error:
        print(error)
        pass 
else:
    print("No decision matching - script exit")
    syslog.syslog(syslog.LOG_INFO, "No decision matching - script exit")
    sys.exit()