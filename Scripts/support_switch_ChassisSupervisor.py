#!/usr/local/bin/python3.7

import sys
import os
import json
from time import strftime, localtime
from support_tools_OmniSwitch import get_credentials, collect_command_output_ps, collect_command_output_fan, collect_command_output_ni, check_save, add_new_save
from support_send_notification import send_message, send_message_request, send_file
from database_conf import *
import re
import syslog

syslog.syslog(syslog.LOG_INFO, "Executing script")


runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

last = ""
with open("/var/log/devices/lastlog_power_supply_down.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_power_supply_down.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_power_supply_down.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
        print(msg)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog IP Address: " + ipadd)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog Hostname: " + host)
        syslog.syslog(syslog.LOG_DEBUG, "Syslog message: " + msg)
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_power_supply_down.json empty")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_power_supply_down.json - JSONDecodeError")
        exit()
    except IndexError:
        print("Index error in regex")
        syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_power_supply_down.json - JSONDecodeError")
        exit()

# always 1
#never -1
# ? 0
save_resp = check_save(ipadd, "1", "power_supply")
save_resp = check_save(ipadd, "2", "power_supply")
save_resp = check_save(ipadd, "Unknown", "power_supply")
save_resp = check_save(ipadd, "", "fan")


if save_resp == "0":
    syslog.syslog(syslog.LOG_INFO, "No Decision saved")
   # Sample log
    # OS6860 swlogd ChassisSupervisor MipMgr EVENT: CUSTLOG CMM chassisTrapsAlert - All power supplies OK
    if "All power supplies" in msg:
        try:
            pattern = "All power supplies"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            ps_status = re.findall(r"All power supplies (.*)", msg)[0]
            subject = ("Preventive Maintenance Application - Power Supply check detected on OmniSwitch: {0} / {1}").format(host,ipadd)
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            action = ("All Power Supplies are {0} on OmniSwitch (Hostname: {1})").format(ps_status,host)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            result = "This log is generated after an unplug/plug of the Power Supply"
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            category = "ps"
            filename_path = "/var/log/devices/lastlog_power_supply_down.json"
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API")
            send_file(filename_path, subject, action, result, category, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
        sys.exit()

    # Sample log
    # OS6860 swlogd ChassisSupervisor fan & temp Mgr ALRT: Chassis Fan Failure
    elif "Fan Failure" in msg:
        try:
            pattern = "Fan Failure"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            fan_id = "Unknown"
            syslog.syslog(syslog.LOG_INFO, " Executing function collect_command_output_fan")
            filename_path, subject, action, result, category = collect_command_output_fan(switch_user, switch_password, fan_id, host, ipadd)
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")            
            send_file(filename_path, subject, action, result, category, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            notif = "Preventive Maintenance Application - Fan unit issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
            answer = send_message_request(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            print(answer)
            if answer == "2":
                add_new_save(ipadd, fan_id, "fan", choice="always")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Fan ID: " + fan_id + " Choice: " + " Always")
            elif answer == "0":
                add_new_save(ipadd, fan_id, "fan", choice="never")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Fan ID: " + fan_id + " Choice: " + " Never")
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Fan_Unit": fan_id}, "fields": {"count": 1}}])
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

    elif "Fan is inoperable" in msg:
        try:
            pattern = "Fan is inoperable"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            fan_id = "Unknown"
            syslog.syslog(syslog.LOG_INFO, " Executing function collect_command_output_fan")
            filename_path, subject, action, result, category = collect_command_output_fan(switch_user, switch_password, fan_id, host, ipadd)
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
            send_file(filename_path, subject, action, result, category, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            notif = "Preventive Maintenance Application - Fan unit issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
            answer = send_message_request(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            print(answer)
            if answer == "2":
                add_new_save(ipadd, fan_id, "fan", choice="always")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Fan ID: " + fan_id + " Choice: " + " Always")
            elif answer == "0":
                add_new_save(ipadd, fan_id, "fan", choice="never")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Fan ID: " + fan_id + " Choice: " + " Never")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Fan_Unit": fan_id}, "fields": {"count": 1}}])
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
    # OS6860 swlogd ChassisSupervisor fan & temp Mgr ERR: Alert: PS2(evac) and Fan(pres) have opposite air flow direction
    elif "have opposite air flow direction" in msg:
        try:
            pattern = "have opposite air flow direction"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            fan_id = "Unknown"
            ps_id, ps_direction, fan_direction = re.findall(r"Alert: (.*)\((.*)\) and Fan\((.*)\) have opposite air flow direction", msg)[0]
            syslog.syslog(syslog.LOG_INFO, " Executing function collect_command_output_fan")
            filename_path, subject, action, result, category = collect_command_output_fan(switch_user, switch_password, fan_id, host, ipadd)

            action = ("The Power Supply unit {0} and Fan have opposite AirFlow direction (Rear to Front / Front to Rear) on OmniSwitch (Hostname: {1})").format(ps_id, host)
            result = "Find enclosed to this notification the log collection for further analysis. More details in the Technical Knowledge Base https://myportal.al-enterprise.com/alebp/s/tkc-redirect?000059004"
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
            send_file(filename_path, subject, action, result, category, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            notif = "Preventive Maintenance Application - Fan unit issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
            answer = send_message_request(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            print(answer)
            if answer == "2":
                add_new_save(ipadd, ps_id, "ps", choice="always")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " PS ID: " + ps_id + " Choice: " + " Always")
            elif answer == "0":
                add_new_save(ipadd, ps_id, "ps", choice="never")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " PS ID: " + ps_id + " Choice: " + " Never")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "PS_Unit": ps_id}, "fields": {"count": 1}}])
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
    # OS6860 ConsLog +++ LM75 temperature read failed , errno :-1
    elif "temperature read failed" in msg:
        try:
            pattern = "temperature read failed"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            fan_id = "Unknown"
            syslog.syslog(syslog.LOG_INFO, " Executing function collect_command_output_fan")
            filename_path, subject, action, result, category = collect_command_output_fan(switch_user, switch_password, fan_id, host, ipadd)

            action = ("A Fan unit is Down or running abnormal on OmniSwitch (Hostname: {0}). These kind of issues are mostly created due to Faulty or Non-ALE certified SFP and QSFP. If the issue is still seen after using a good ALE-Certified SFP and QSFP, please upgrade the CPUCPLD.").format(fan_id, host)
            result = "Find enclosed to this notification the log collection for further analysis. More details in the Technical Knowledge Base https://myportal.al-enterprise.com/alebp/s/tkc-redirect?000065410."
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
            send_file(filename_path, subject, action, result, category, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            
            notif = "Preventive Maintenance Application - Fan unit issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
            answer = send_message_request(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            print(answer)
            if answer == "2":
                add_new_save(ipadd, fan_id, "fan", choice="always")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Fan ID: " + fan_id + " Choice: " + " Always")
            elif answer == "0":
                add_new_save(ipadd, fan_id, "fan", choice="never")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Fan ID: " + fan_id + " Choice: " + " Never")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Fan_Unit": fan_id}, "fields": {"count": 1}}])
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

    # Sample log (PR reference CRAOS8X-4836)
    # OS6860 swlogd ChassisSupervisor bootMgr ALRT: Secondary CMM Fabric PCIe links failed to come up  - rebooting
    elif "CMM Fabric" in msg:
        try:
            pattern = "CMM Fabric"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            cmm, reason = re.findall(r"ALRT: (.*?) CMM Fabric (.*?)  - rebooting", msg)[0]
            notif = ("Preventive Maintenance Application - The {0} CMM is rebooting on OmniSwitch {1} / {2}.\n\nReason:\n- {3}\nIf CFM is inoperable the CMM will not come UP.").format(cmm,host,ipadd,reason)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification:" + notif) 
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send Message") 
            send_message(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Notification sent")

            notif = "Preventive Maintenance Application - NI Module unit issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
            answer = send_message_request(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            print(answer)
            if answer == "2":
                add_new_save(ipadd, cmm, "cmm", choice="always")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " CMM ID: " + cmm + " Choice: " + " Always")
            elif answer == "0":
                add_new_save(ipadd, cmm, "cmm", choice="never")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " CMM ID: " + cmm + " Choice: " + " Never")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "CMM_Unit": cmm}, "fields": {"count": 1}}])
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

    # Sample log (PR reference CRAOS8X-19743)
    # OS6860 swlogd ChassisSupervisor vcReloadMgr ERR: vcReloadMgrRcvCallback: verify failed for chassis 2 reason Image verification failure on slave chassis
    elif "Image verification failure" in msg:
        try:
            pattern = "Image verification failure"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            cmm_id, cmm = re.findall(r"verify failed for chassis (.*?) reason Image verification failure on (.*?) chassis", msg)[0]
            notif = ("Preventive Maintenance Application - The {0} CMM ID {1} does not reload on OmniSwitch {2} / {3}.\n\nReason: Image verification failure.").format(cmm,cmm_id,host,ipadd)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification:" + notif) 
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send Message") 
            send_message(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            notif = "Preventive Maintenance Application - NI Module unit issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
            answer = send_message_request(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            print(answer)
            if answer == "2":
                add_new_save(ipadd, cmm_id, "cmm", choice="always")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " CMM ID: " + cmm_id + " Choice: " + " Always")
            elif answer == "0":
                add_new_save(ipadd, cmm_id, "cmm", choice="never")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " CMM ID: " + cmm_id + " Choice: " + " Never")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "CMM_Unit": cmm_id}, "fields": {"count": 1}}])
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

    # Sample log (PR reference CRAOS8X-28368)
    # OS6860 swlogd ChassisSupervisor niMgr ALRT: Incompatible expansion module on ni 2, powered down
    elif "Incompatible expansion module" in msg:
        try:
            pattern = "Incompatible expansion module"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            ni_id = re.findall(r"Incompatible expansion module on ni (.*?), powered down", msg)[0]
            syslog.syslog(syslog.LOG_INFO, " Executing function collect_command_output_ni")
            filename_path, subject, action, result, category = collect_command_output_ni(switch_user, switch_password, ni_id, host, ipadd)
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
            send_file(filename_path, subject, action, result, category, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            notif = "Preventive Maintenance Application - NI Module unit issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
            answer = send_message_request(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            print(answer)
            if answer == "2":
                add_new_save(ipadd, ni_id, "ni", choice="always")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " NI ID: " + ni_id + " Choice: " + " Always")
            elif answer == "0":
                add_new_save(ipadd, ni_id, "ni", choice="never")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " NI ID: " + ni_id + " Choice: " + " Never")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "NI_Unit": ni_id}, "fields": {"count": 1}}])
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
    # OS6860 swlogd ChassisSupervisor fan & temp Mgr ERR: fan 3 runs below specified speed. fan_load=35, low_count=0xa
    elif "runs below specified speed" in msg:
        try:
            pattern = "runs below specified speed"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            fan_id = re.findall(r"ERR: fan (.*?) runs below specified speed", msg)[0]
            syslog.syslog(syslog.LOG_INFO, " Executing function collect_command_output_fan")
            filename_path, subject, action, result, category = collect_command_output_fan(switch_user, switch_password, fan_id, host, ipadd)

            action = ("The Fan unit {0} is Down or running abnormal on OmniSwitch (Hostname: {1})").format(fan_id, host)
            result = "Find enclosed to this notification the log collection for further analysis. Please replace the faulty FAN as soon as possible."
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
            send_file(filename_path, subject, action, result, category, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            notif = "Preventive Maintenance Application - Fan unit issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
            answer = send_message_request(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            print(answer)
            if answer == "2":
                add_new_save(ipadd, fan_id, "fan", choice="always")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Fan ID: " + fan_id + " Choice: " + " Always")
            elif answer == "0":
                add_new_save(ipadd, fan_id, "fan", choice="never")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Fan ID: " + fan_id + " Choice: " + " Never")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Fan_Unit": fan_id}, "fields": {"count": 1}}])
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
    # OS6860 swlogd ChassisSupervisor fan & temp Mgr INFO: Alert: PS1 airFlow unknown yet
    elif "airFlow unknown yet" in msg:
        try:
            pattern = "airFlow unknown yet"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            nb_power_supply = re.findall(r"Alert: (.*?) airFlow unknown yet", msg)[0]
            if nb_power_supply == "PS1":
                nb_power_supply = 1
            if nb_power_supply == "PS2":
                nb_power_supply = 2
            syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_ps")
            filename_path, subject, action, result, category = collect_command_output_ps(switch_user, switch_password, nb_power_supply, host, ipadd)
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
            send_file(filename_path, subject, action, result, category, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            notif = "Preventive Maintenance Application - Power Supply issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
            answer = send_message_request(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            print(answer)
            if answer == "2":
                add_new_save(ipadd, nb_power_supply, "power_supply", choice="always")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " PS ID: " + nb_power_supply + " Choice: " + " Always")
            elif answer == "0":
                add_new_save(ipadd, nb_power_supply, "power_supply", choice="never")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " PS ID: " + nb_power_supply + " Choice: " + " Never")
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "PS_Unit": nb_power_supply}, "fields": {"count": 1}}])
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
    # OS6860 swlogd ChassisSupervisor fpgaMgr ERR message: +++ Unsupported power supply detected in PS1.
    elif "Unsupported power supply" in msg:
        try:
            pattern = "Unsupported power supply"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            nb_power_supply = re.findall(r"Unsupported power supply detected in (.*?).", msg)[0]
            if nb_power_supply == "PS1":
                nb_power_supply = 1
            if nb_power_supply == "PS2":
                nb_power_supply = 2
            syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_ps")
            filename_path, subject, action, result, category = collect_command_output_ps(switch_user, switch_password, nb_power_supply, host, ipadd)
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
            send_file(filename_path, subject, action, result, category, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            notif = "Preventive Maintenance Application - Power Supply issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
            answer = send_message_request(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            print(answer)
            if answer == "2":
                add_new_save(ipadd, nb_power_supply, "power_supply", choice="always")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " PS ID: " + nb_power_supply + " Choice: " + " Always")
            elif answer == "0":
                add_new_save(ipadd, nb_power_supply, "power_supply", choice="never")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " PS ID: " + nb_power_supply + " Choice: " + " Never")
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "PS_Unit": nb_power_supply}, "fields": {"count": 1}}])
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
    # OS6860E swlogd ChassisSupervisor Power Mgr INFO: Power Supply 1 Removed
    elif "Removed" in msg:
        try:
            pattern = "Removed"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            nb_power_supply = re.findall(r"Power Supply (.*?) Removed", msg)[0]
            syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_ps")
            filename_path, subject, action, result, category = collect_command_output_ps(switch_user, switch_password, nb_power_supply, host, ipadd)
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
            send_file(filename_path, subject, action, result, category, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            notif = "Preventive Maintenance Application - Power Supply issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
            answer = send_message_request(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            print(answer)
            if answer == "2":
                add_new_save(ipadd, nb_power_supply, "power_supply", choice="always")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " PS ID: " + nb_power_supply + " Choice: " + " Always")
            elif answer == "0":
                add_new_save(ipadd, nb_power_supply, "power_supply", choice="never")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " PS ID: " + nb_power_supply + " Choice: " + " Never")
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "PS_Unit": nb_power_supply}, "fields": {"count": 1}}])
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
    # OS6860E swlogd ChassisSupervisor MipMgr EVENT: CUSTLOG CMM chassisTrapsAlert - Power supply is inoperable: PS 2
    elif "inoperable" in msg:
        try:
            pattern = "inoperable"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            nb_power_supply = re.findall(r"Power supply is inoperable: PS (.*)", msg)[0]
            syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_ps")
            filename_path, subject, action, result, category = collect_command_output_ps(switch_user, switch_password, nb_power_supply, host, ipadd)
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
            send_file(filename_path, subject, action, result, category, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            notif = "Preventive Maintenance Application - Power Supply issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
            answer = send_message_request(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            print(answer)
            if answer == "2":
                add_new_save(ipadd, nb_power_supply, "power_supply", choice="always")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " PS ID: " + nb_power_supply + " Choice: " + " Always")
            elif answer == "0":
                add_new_save(ipadd, nb_power_supply, "power_supply", choice="never")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " PS ID: " + nb_power_supply + " Choice: " + " Never")
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "PS_Unit": nb_power_supply}, "fields": {"count": 1}}])
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
    # OS6860E swlogd ChassisSupervisor MipMgr EVENT: CUSTLOG CMM Device Power Supply operational state changed to UNPOWERED
    elif "UNPOWERED" in msg:
        try:
            pattern = "UNPOWERED"
            syslog.syslog(syslog.LOG_INFO, "Pattern matching: " + pattern)
            nb_power_supply = "Unknown"
            syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_ps")
            filename_path, subject, action, result, category = collect_command_output_ps(switch_user, switch_password, nb_power_supply, host, ipadd)
            syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
            syslog.syslog(syslog.LOG_INFO, "Action: " + action)
            syslog.syslog(syslog.LOG_INFO, "Result: " + result)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
            send_file(filename_path, subject, action, result, category, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            notif = "Preventive Maintenance Application - Power Supply issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow Adaptive Card")
            answer = send_message_request(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            print(answer)
            if answer == "2":
                add_new_save(ipadd, nb_power_supply, "power_supply", choice="always")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " PS ID: " + nb_power_supply + " Choice: " + " Always")
            elif answer == "0":
                add_new_save(ipadd, nb_power_supply, "power_supply", choice="never")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " PS ID: " + nb_power_supply + " Choice: " + " Never")
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename( __file__)), "tags": {"IP": ipadd, "PS_Unit": "All"}, "fields": {"count": 1}}])
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
    else:
        print("no pattern match - exiting script")
        syslog.syslog(syslog.LOG_INFO, "no pattern match - exiting script")
        sys.exit()      

elif save_resp == "-1":
    print("Decision saved to No - script exit")
    syslog.syslog(syslog.LOG_INFO, "Decision saved to No - script exit")
    sys.exit()

elif save_resp == "1":
    answer = '2'
    print("Decision saved to Yes and remember")
    syslog.syslog(syslog.LOG_INFO, "Decision saved to Yes and remember")
else:
    answer = '1'
    syslog.syslog(syslog.LOG_INFO, "No answer - Decision set to Yes - Script exit - will be called by next occurence")    

syslog.syslog(syslog.LOG_INFO, "Rainbow Acaptive Card answer: " + answer)

if answer == '2':
    syslog.syslog(syslog.LOG_INFO, "Decision is Yes and Remember - We are doing log collection")
    nb_power_supply == "Unknown"
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_ps")
    filename_path, subject, action, result, category = collect_command_output_ps(switch_user, switch_password, nb_power_supply, host, ipadd)
    subject = ("Preventive Maintenance Application - Hardware issue detected on OmniSwitch: {0} / {1}").format(host,ipadd)
    action = ("A Power Supply or Fan unit  is Down or running abnormal  on OmniSwitch (Hostname: {0})").format(host)
    result = "Find enclosed to this notification the log collection for further analysis."
    syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
    syslog.syslog(syslog.LOG_INFO, "Action: " + action)
    syslog.syslog(syslog.LOG_INFO, "Result: " + result)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
    send_file(filename_path, subject, action, result, category, jid)
    syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
else:
    print("No decision matching - script exit")
    syslog.syslog(syslog.LOG_INFO, "No decision matching - script exit")
    sys.exit()
