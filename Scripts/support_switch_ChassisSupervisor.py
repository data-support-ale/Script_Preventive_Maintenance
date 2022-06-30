#!/usr/local/bin/python3.7

import sys
import os
import json
from time import strftime, localtime
from support_tools_OmniSwitch import get_credentials, collect_command_output_ps, collect_command_output_fan, collect_command_output_ni, check_save, add_new_save
from support_send_notification import send_message, send_message_request, send_file
from database_conf import *
import re

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())
script_name = sys.argv[0]
logging = "logger -t montag -p user.info Executing script {0}".format(script_name)
try:
    os.system('logger -t montag -p user.info ' + logging)
except:
    pass
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
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_power_supply_down.json empty")
        exit()
    except IndexError:
        print("Index error in regex")
        exit()

# always 1
#never -1
# ? 0
save_resp = check_save(ipadd, "1", "power_supply")
save_resp = check_save(ipadd, "2", "power_supply")
save_resp = check_save(ipadd, "Unknown", "power_supply")
save_resp = check_save(ipadd, "", "fan")


if save_resp == "0":
   # Sample log
    # OS6860 swlogd ChassisSupervisor MipMgr EVENT: CUSTLOG CMM chassisTrapsAlert - All power supplies OK
    if "All power supplies" in msg:
        try:
            pattern = "All power supplies"
            logging = "logger -t montag -p user.info Executing script {0} - pattern detected: {1}".format(script_name,pattern)
            try:
                os.system('logger -t montag -p user.info ' + logging)
            except:
                pass
            ps_status = re.findall(r"All power supplies (.*)", msg)[0]
            subject = ("Preventive Maintenance Application - Power Supply check detected on OmniSwitch: {0} / {1}").format(host,ipadd)
            action = ("All Power Supplies are {0} on OmniSwitch (Hostname: {1})").format(ps_status,host)
            result = "This log is generated after an unplug/plug of the Power Supply"
            category = "ps"
            filename_path = "/var/log/devices/lastlog_power_supply_down.json"
            send_file(filename_path, subject, action, result, category, jid)
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
        sys.exit()

    # Sample log
    # OS6860 swlogd ChassisSupervisor fan & temp Mgr ALRT: Chassis Fan Failure
    if "Fan Failure" in msg:
        try:
            pattern = "Fan Failure"
            logging = "logger -t montag -p user.info Executing script {0} - pattern detected: {1}".format(script_name,pattern)
            try:
                os.system('logger -t montag -p user.info ' + logging)
            except:
                pass
            fan_id = "Unknown"
            filename_path, subject, action, result, category = collect_command_output_fan(switch_user, switch_password, fan_id, host, ipadd)
            send_file(filename_path, subject, action, result, category, jid)

            notif = "Preventive Maintenance Application - Fan unit issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            answer = send_message_request(notif, jid)

            print(answer)
            if answer == "2":
                add_new_save(ipadd, fan_id, "fan", choice="always")
            elif answer == "0":
                add_new_save(ipadd, fan_id, "fan", choice="never")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Fan_Unit": fan_id}, "fields": {"count": 1}}])
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

    if "Fan is inoperable" in msg:
        try:
            pattern = "Fan is inoperable"
            logging = "logger -t montag -p user.info Executing script {0} - pattern detected: {1}".format(script_name,pattern)
            try:
                os.system('logger -t montag -p user.info ' + logging)
            except:
                pass
            fan_id = "Unknown"
            filename_path, subject, action, result, category = collect_command_output_fan(switch_user, switch_password, fan_id, host, ipadd)
            send_file(filename_path, subject, action, result, category, jid)

            notif = "Preventive Maintenance Application - Fan unit issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            answer = send_message_request(notif, jid)

            print(answer)
            if answer == "2":
                add_new_save(ipadd, fan_id, "fan", choice="always")
            elif answer == "0":
                add_new_save(ipadd, fan_id, "fan", choice="never")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Fan_Unit": fan_id}, "fields": {"count": 1}}])
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
    if "have opposite air flow direction" in msg:
        try:
            pattern = "have opposite air flow direction"
            logging = "logger -t montag -p user.info Executing script {0} - pattern detected: {1}".format(script_name,pattern)
            try:
                os.system('logger -t montag -p user.info ' + logging)
            except:
                pass
            fan_id = "Unknown"
            ps_id, ps_direction, fan_direction = re.findall(r"Alert: (.*)\((.*)\) and Fan\((.*)\) have opposite air flow direction", msg)[0]
            filename_path, subject, action, result, category = collect_command_output_fan(switch_user, switch_password, fan_id, host, ipadd)

            action = ("The Power Supply unit {0} and Fan have opposite AirFlow direction (Rear to Front / Front to Rear) on OmniSwitch (Hostname: {1})").format(ps_id, host)
            result = "Find enclosed to this notification the log collection for further analysis. More details in the Technical Knowledge Base https://myportal.al-enterprise.com/alebp/s/tkc-redirect?000059004"
            send_file(filename_path, subject, action, result, category, jid)

            notif = "Preventive Maintenance Application - Fan unit issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            answer = send_message_request(notif, jid)
            print(answer)
            if answer == "2":
                add_new_save(ipadd, fan_id, "fan", choice="always")
            elif answer == "0":
                add_new_save(ipadd, fan_id, "fan", choice="never")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "PS_Unit": ps_id}, "fields": {"count": 1}}])
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
    if "temperature read failed" in msg:
        try:
            pattern = "temperature read failed"
            logging = "logger -t montag -p user.info Executing script {0} - pattern detected: {1}".format(script_name,pattern)
            try:
                os.system('logger -t montag -p user.info ' + logging)
            except:
                pass
            fan_id = "Unknown"
            filename_path, subject, action, result, category = collect_command_output_fan(switch_user, switch_password, fan_id, host, ipadd)

            action = ("A Fan unit is Down or running abnormal on OmniSwitch (Hostname: {0}). These kind of issues are mostly created due to Faulty or Non-ALE certified SFP and QSFP. If the issue is still seen after using a good ALE-Certified SFP and QSFP, please upgrade the CPUCPLD.").format(fan_id, host)
            result = "Find enclosed to this notification the log collection for further analysis. More details in the Technical Knowledge Base https://myportal.al-enterprise.com/alebp/s/tkc-redirect?000065410."
            send_file(filename_path, subject, action, result, category, jid)
            
            notif = "Preventive Maintenance Application - Fan unit issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            answer = send_message_request(notif, jid)
            print(answer)
            if answer == "2":
                add_new_save(ipadd, fan_id, "fan", choice="always")
            elif answer == "0":
                add_new_save(ipadd, fan_id, "fan", choice="never")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Fan_Unit": fan_id}, "fields": {"count": 1}}])
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
    if "CMM Fabric" in msg:
        try:
            pattern = "CMM Fabric"
            logging = "logger -t montag -p user.info Executing script {0} - pattern detected: {1}".format(script_name,pattern)
            try:
                os.system('logger -t montag -p user.info ' + logging)
            except:
                pass
            cmm, reason = re.findall(r"ALRT: (.*?) CMM Fabric (.*?)  - rebooting", msg)[0]
            notif = ("Preventive Maintenance Application - The {0} CMM is rebooting on OmniSwitch {1} / {2}.\n\nReason:\n- {3}\nIf CFM is inoperable the CMM will not come UP.").format(cmm,host,ipadd,reason)
            send_message(notif, jid)

            notif = "Preventive Maintenance Application - NI Module unit issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            answer = send_message_request(notif, jid)
            print(answer)
            if answer == "2":
                add_new_save(ipadd, cmm, "cmm", choice="always")
            elif answer == "0":
                add_new_save(ipadd, cmm, "cmm", choice="never")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "CMM_Unit": cmm}, "fields": {"count": 1}}])
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
    if "Image verification failure" in msg:
        try:
            pattern = "Image verification failure"
            logging = "logger -t montag -p user.info Executing script {0} - pattern detected: {1}".format(script_name,pattern)
            try:
                os.system('logger -t montag -p user.info ' + logging)
            except:
                pass
            cmm_id, cmm = re.findall(r"verify failed for chassis (.*?) reason Image verification failure on (.*?) chassis", msg)[0]
            notif = ("Preventive Maintenance Application - The {0} CMM ID {1} does not reload on OmniSwitch {2} / {3}.\n\nReason: Image verification failure.").format(cmm,cmm_id,host,ipadd)
            send_message(notif, jid)

            notif = "Preventive Maintenance Application - NI Module unit issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            answer = send_message_request(notif, jid)
            print(answer)
            if answer == "2":
                add_new_save(ipadd, cmm, "cmm", choice="always")
            elif answer == "0":
                add_new_save(ipadd, cmm, "cmm", choice="never")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "CMM_Unit": cmm}, "fields": {"count": 1}}])
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
    if "Incompatible expansion module" in msg:
        try:
            pattern = "Incompatible expansion module"
            logging = "logger -t montag -p user.info Executing script {0} - pattern detected: {1}".format(script_name,pattern)
            try:
                os.system('logger -t montag -p user.info ' + logging)
            except:
                pass
            ni_id = re.findall(r"Incompatible expansion module on ni (.*?), powered down", msg)[0]
            filename_path, subject, action, result, category = collect_command_output_ni(switch_user, switch_password, ni_id, host, ipadd)
            send_file(filename_path, subject, action, result, category, jid)

            notif = "Preventive Maintenance Application - NI Module unit issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            answer = send_message_request(notif, jid)
            print(answer)
            if answer == "2":
                add_new_save(ipadd, ni_id, "ni", choice="always")
            elif answer == "0":
                add_new_save(ipadd, ni_id, "ni", choice="never")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "NI_Unit": ni_id}, "fields": {"count": 1}}])
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
    if "runs below specified speed" in msg:
        try:
            pattern = "runs below specified speed"
            logging = "logger -t montag -p user.info Executing script {0} - pattern detected: {1}".format(script_name,pattern)
            try:
                os.system('logger -t montag -p user.info ' + logging)
            except:
                pass
            fan_id = re.findall(r"ERR: fan (.*?) runs below specified speed", msg)[0]
            filename_path, subject, action, result, category = collect_command_output_fan(switch_user, switch_password, fan_id, host, ipadd)

            action = ("The Fan unit {0} is Down or running abnormal on OmniSwitch (Hostname: {1})").format(fan_id, host)
            result = "Find enclosed to this notification the log collection for further analysis. Please replace the faulty FAN as soon as possible."
            send_file(filename_path, subject, action, result, category, jid)

            notif = "Preventive Maintenance Application - Fan unit issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            answer = send_message_request(notif, jid)
            print(answer)
            if answer == "2":
                add_new_save(ipadd, fan_id, "fan", choice="always")
            elif answer == "0":
                add_new_save(ipadd, fan_id, "fan", choice="never")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "Fan_Unit": fan_id}, "fields": {"count": 1}}])
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
    if "airFlow unknown yet" in msg:
        try:
            pattern = "airFlow unknown yet"
            logging = "logger -t montag -p user.info Executing script {0} - pattern detected: {1}".format(script_name,pattern)
            try:
                os.system('logger -t montag -p user.info ' + logging)
            except:
                pass
            nb_power_supply = re.findall(r"Alert: (.*?) airFlow unknown yet", msg)[0]
            if nb_power_supply == "PS1":
                nb_power_supply = 1
            if nb_power_supply == "PS2":
                nb_power_supply = 2
            filename_path, subject, action, result, category = collect_command_output_ps(switch_user, switch_password, nb_power_supply, host, ipadd)
            send_file(filename_path, subject, action, result, category, jid)
#            info = "A default on Power supply {} from device {} has been detected".format(nb_power_supply, ipadd)
#            send_message(info, jid)

            notif = "Preventive Maintenance Application - Power Supply issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            answer = send_message_request(notif, jid)
            print(answer)
            if answer == "2":
                add_new_save(ipadd, nb_power_supply, "power_supply", choice="always")
            elif answer == "0":
                add_new_save(ipadd, nb_power_supply, "power_supply", choice="never")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "PS_Unit": nb_power_supply}, "fields": {"count": 1}}])
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
    if "Removed" in msg:
        try:
            pattern = "Removed"
            logging = "logger -t montag -p user.info Executing script {0} - pattern detected: {1}".format(script_name,pattern)
            try:
                os.system('logger -t montag -p user.info ' + logging)
            except:
                pass
            nb_power_supply = re.findall(r"Power Supply (.*?) Removed", msg)[0]
            filename_path, subject, action, result, category = collect_command_output_ps(switch_user, switch_password, nb_power_supply, host, ipadd)
            send_file(filename_path, subject, action, result, category, jid)
#            info = "A default on Power supply {} from device {} has been detected".format(nb_power_supply, ipadd)
#            send_message(info, jid)

            notif = "Preventive Maintenance Application - Power Supply issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            answer = send_message_request(notif, jid)
            print(answer)
            if answer == "2":
                add_new_save(ipadd, nb_power_supply, "power_supply", choice="always")
            elif answer == "0":
                add_new_save(ipadd, nb_power_supply, "power_supply", choice="never")

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "PS_Unit": nb_power_supply}, "fields": {"count": 1}}])
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
            logging = "logger -t montag -p user.info Executing script {0} - pattern detected: {1}".format(script_name,pattern)
            try:
                os.system('logger -t montag -p user.info ' + logging)
            except:
                pass
            nb_power_supply = re.findall(r"Power supply is inoperable: PS (.*)", msg)[0]
            filename_path, subject, action, result, category = collect_command_output_ps(switch_user, switch_password, nb_power_supply, host, ipadd)
            send_file(filename_path, subject, action, result, category, jid)
#            info = "A default on Power supply {} from device {} has been detected".format(nb_power_supply, ipadd)
#            send_message(info, jid)

            notif = "Preventive Maintenance Application - Power Supply issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            answer = send_message_request(notif, jid)
            print(answer)
            if answer == "2":
                add_new_save(ipadd, nb_power_supply, "power_supply", choice="always")
            elif answer == "0":
                add_new_save(ipadd, nb_power_supply, "power_supply", choice="never")


            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "PS_Unit": nb_power_supply}, "fields": {"count": 1}}])
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
            logging = "logger -t montag -p user.info Executing script {0} - pattern detected: {1}".format(script_name,pattern)
            try:
                os.system('logger -t montag -p user.info ' + logging)
            except:
                pass
            nb_power_supply = "Unknown"
            filename_path, subject, action, result, category = collect_command_output_ps(switch_user, switch_password, nb_power_supply, host, ipadd)
            send_file(filename_path, subject, action, result, category, jid)
#            info = "A default on Power supply \"Power Supply operational state changed to UNPOWERED\" from device {} has been detected".format(ipadd)
#            send_message(info, jid)

            notif = "Preventive Maintenance Application - Power Supply issue detected on OmniSwitch " + host + ".\nDo you want to keep being notified? " + ip_server        #send_message(info, jid)
            answer = send_message_request(notif, jid)
            print(answer)
            if answer == "2":
                add_new_save(ipadd, nb_power_supply, "power_supply", choice="always")
            elif answer == "0":
                add_new_save(ipadd, nb_power_supply, "power_supply", choice="never")


            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename( __file__)), "tags": {"IP": ipadd, "PS_Unit": "All"}, "fields": {"count": 1}}])
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

elif save_resp == "-1":
        print("Decision set to never - exit")
        sys.exit()

elif save_resp == "1":
    answer = '2'
else:
    answer = '1'

if answer == '1':
    if "Removed" in msg:
        try:
            nb_power_supply = re.findall(r"Power Supply (.*?) Removed", msg)[0]
            filename_path, subject, action, result, category = collect_command_output_ps(switch_user, switch_password, nb_power_supply, host, ipadd)
            send_file(filename_path, subject, action, result, category, jid)
#            info = "A default on Power supply {} from device {} has been detected".format(nb_power_supply, ipadd)
#            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "PS_Unit": nb_power_supply}, "fields": {"count": 1}}])
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
            nb_power_supply = re.findall(r"Power supply is inoperable: PS (.*)", msg)[0]
            filename_path, subject, action, result, category = collect_command_output_ps(switch_user, switch_password, nb_power_supply, host, ipadd)
            send_file(filename_path, subject, action, result, category, jid)
#            info = "A default on Power supply {} from device {} has been detected".format(nb_power_supply, ipadd)
#            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "PS_Unit": nb_power_supply}, "fields": {"count": 1}}])
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
            nb_power_supply = "Unknown"
            filename_path, subject, action, result, category = collect_command_output_ps(switch_user, switch_password, nb_power_supply, host, ipadd)
            send_file(filename_path, subject, action, result, category, jid)
#            info = "A default on Power supply \"Power Supply operational state changed to UNPOWERED\" from device {} has been detected".format(ipadd)
#            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename( __file__)), "tags": {"IP": ipadd, "PS_Unit": "All"}, "fields": {"count": 1}}])
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