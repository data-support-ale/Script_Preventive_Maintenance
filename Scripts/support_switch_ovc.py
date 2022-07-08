#!/usr/local/bin/python3.7

import sys
import os
import json
from time import strftime, localtime
from support_tools_OmniSwitch import get_credentials, send_file, collect_command_output_ovc, check_save, add_new_save, ssh_connectivity_check
from support_send_notification import send_message, send_message_request_advanced
from database_conf import *
import re
import syslog

syslog.openlog('support_switch_ovcirrus')
syslog.syslog(syslog.LOG_INFO, "Executing script")


runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

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
    syslog.syslog(syslog.LOG_INFO, "Executing function check_save")
    save_resp = check_save(ipadd, 0, "cloud_agent")
    # Sample log
    # OS6860E swlogd OPENVPN(168) Data: TCP: connect to [AF_INET]18.194.174.46:443 failed: S_errno_EHOSTUNREACH
    if "S_errno_EHOSTUNREACH" in msg:
        pattern = "S_errno_EHOSTUNREACH"
        syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
        if save_resp == "-1":
            print("Decision saved to No - script exit")
            syslog.syslog(syslog.LOG_INFO, "Decision saved to No - script exit")
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "VPN": "Unknown", "Reason": "S_errno_EHOSTUNREACH"}, "fields": {"count": 1}}]) 
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
                sys.exit()       
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                sys.exit() 
        try:
            vpn_ip, reason = re.findall(r"\[AF_INET\](.*?):443 failed: (.*)", msg)[0]
            print(vpn_ip)
            print(reason)
            filename_path, subject, action, result, category = collect_command_output_ovc(switch_user, switch_password, vpn_ip, reason, host, ipadd)
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
            send_file(filename_path, subject, action, result, category, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "VPN": vpn_ip, "Reason": reason}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
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
    # Sample log
    # OS6860E swlogd OPENVPN(168) Data: TCP: connect to [AF_INET]18.194.174.46:443 failed: S_errno_ETIMEDOUT
    elif "S_errno_ETIMEDOUT" in msg:
        pattern = "S_errno_ETIMEDOUT"
        syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
        if save_resp == "-1":
            print("Decision saved to No - script exit")
            syslog.syslog(syslog.LOG_INFO, "Decision saved to No - script exit")
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "VPN": "Unknown", "Reason": "S_errno_ETIMEDOUT"}, "fields": {"count": 1}}]) 
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
                sys.exit()       
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                sys.exit() 
        try:
            vpn_ip, reason = re.findall(r"[AF_INET](.*?):443 failed: (.*)", msg)[0]
            filename_path, subject, action, result, category = collect_command_output_ovc(switch_user, switch_password, vpn_ip, reason, host, ipadd)
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
            send_file(filename_path, subject, action, result, category, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "VPN": vpn_ip, "Reason": reason}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
                sys.exit() 
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
    # Sample log
    # OS6860E swlogd openvpn[17911] RESOLVE: Cannot resolve host address: psza60a0ivu6v2.tenant.vpn.myovcloud.com:443 (Temporary failure in name resolution)
    elif "Cannot resolve host address" in msg:
        pattern = "Cannot resolve host address"
        syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
        if save_resp == "-1":
            print("Decision saved to No - script exit")
            syslog.syslog(syslog.LOG_INFO, "Decision saved to No - script exit")
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "VPN": "Unknown", "Reason": "Cannot resolve host address"}, "fields": {"count": 1}}]) 
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
                sys.exit()     
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                sys.exit() 
        try:
            vpn_ip= re.findall(r"Cannot resolve host address: (.*?):443", msg)[0]
            reason = "Cannot resolve host address"
            filename_path, subject, action, result, category = collect_command_output_ovc(switch_user, switch_password, vpn_ip, reason, host, ipadd)
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
            send_file(filename_path, subject, action, result, category, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "VPN": vpn_ip, "Reason": reason}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
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
    # Sample log
    # OS6860E swlogd ovcCmm OVCloud ERR: ovcProcessCallHomeResponseSuccess: Invalid process status
    elif "Invalid process status" in msg:
        pattern = "Invalid process status"
        syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
        if save_resp == "-1":
            print("Decision saved to No - script exit")
            syslog.syslog(syslog.LOG_INFO, "Decision saved to No - script exit")
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "VPN": "Unknown", "Reason": "Invalid process status"}, "fields": {"count": 1}}]) 
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
                sys.exit()       
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                sys.exit() 
            
        try:
            reason = "Invalid process status"
            vpn_ip = "0"
            filename_path, subject, action, result, category = collect_command_output_ovc(switch_user, switch_password, vpn_ip, reason, host, ipadd)
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
            send_file(filename_path, subject, action, result, category, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "VPN": vpn_ip, "Reason": reason}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
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
    # Sample log
    # OS6860E OPENVPN(168) Data: Fatal TLS error (check_tls_errors_co), restarting
    elif "Fatal TLS error" in msg:
        pattern = "Fatal TLS error"
        syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
        if save_resp == "-1":
            print("Decision saved to No - script exit")
            syslog.syslog(syslog.LOG_INFO, "Decision saved to No - script exit")
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "VPN": "Unknown", "Reason": "Fatal TLS error"}, "fields": {"count": 1}}]) 
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
                sys.exit()      
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                sys.exit() 
            
        try:
            reason = "Fatal TLS error"
            vpn_ip = "0"
            notif = "Preventive Maintenance Application - A Fatal TLS error has been detected on OmniSwitch (IP : {0} / {1}) syslogs on the OPENVPN task.\nPlease check the certificate status (must be Consistent).\nAs a workaround you can restart the cloud-agent (cloud-agent admin-state restart).".format(ipadd, host)
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
            send_message(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "VPN": vpn_ip, "Reason": reason}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass 
            filename_path, subject, action, result, category = collect_command_output_ovc(switch_user, switch_password, vpn_ip, reason, host, ipadd)
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
            send_file(filename_path, subject, action, result, category, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")


        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
    else:
        print("no pattern match - exiting script")
        sys.exit()



if save_resp == "0":
        syslog.syslog(syslog.LOG_INFO, "No Decision saved")
        if reason == "S_errno_EHOSTUNREACH" or reason == "S_errno_ETIMEDOUT":
            feature = "Restart Cloud-Agent"
            notif = "An OpenVPN issue is detected on OmniSwitch " + host + " reason: " + reason + ".\nDo you want to disable the Cloud-Agent on this switch? This command will result in device being disconnected from OV in cloud." + ip_server
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Rainbow Adaptive Card of type Advanced")
            answer = send_message_request_advanced(notif, jid,feature)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            syslog.syslog(syslog.LOG_INFO, "Rainbow Adaptive Card Answer: " + answer)
            print(answer)
            if answer == "2":
                add_new_save(ipadd, "0", "cloud_agent", choice="always")
            elif answer == "0":
                add_new_save(ipadd, "0", "cloud_agent", choice="never")       
        else:
            feature = "Restart Cloud-Agent"
            notif = "A Cloud-Agent issue is detected on OmniSwitch " + host + " reason: " + reason + ".\nDo you want to disable the Cloud-Agent on this switch? This command will result in device being disconnected from OV in cloud. " + ip_server
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Rainbow Adaptive Card of type Advanced")
            answer = send_message_request_advanced(notif, jid,feature)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            syslog.syslog(syslog.LOG_INFO, "Rainbow Adaptive Card Answer: " + answer)
            print(answer)
            if answer == "2":
                add_new_save(ipadd, "0", "cloud_agent", choice="always")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Choice: " + " Always")

            elif answer == "0":
                add_new_save(ipadd, "0", "cloud_agent", choice="never")             
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Choice: " + " Never")

elif save_resp == "-1":
    print("Decision saved to No - script exit")
    syslog.syslog(syslog.LOG_INFO, "Decision saved to No - script exit")
    try:
        print(vpn_ip)
        print(reason)
        print(ipadd)
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "VPN": vpn_ip, "Reason": reason}, "fields": {"count": 1}}])       
        syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        sys.exit()   
    except UnboundLocalError as error:
       print(error)
       sys.exit()
    except Exception as error:
        print(error)
        sys.exit() 
        
elif save_resp == "1":
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
    answer = send_message(notif, jid)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")       

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
    answer = send_message(notif, jid)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent") 

else:
    print("No decision matching - script exit")
    syslog.syslog(syslog.LOG_INFO, "No decision matching - script exit")
    sys.exit() 