#!/usr/local/bin/python3.7
import sys
import json

from support_tools_OmniSwitch import debugging, get_credentials, collect_command_output_network_loop, add_new_save, check_save, ssh_connectivity_check, script_has_run_recently
from time import strftime, localtime, sleep
from datetime import datetime, timedelta
import re
from support_send_notification import *
from database_conf import *
import syslog

# Script init
script_name = sys.argv[0]
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

syslog.openlog('support_switch_loop')
syslog.syslog(syslog.LOG_INFO, "Executing script")

# Get informations from logs.
switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()


def process(ipadd, hostname, port, agg):
    syslog.syslog(syslog.LOG_DEBUG, "Process function called with " + " IP Address :" + ipadd + " OmniSwitch hostname :" + hostname + " Port :" + port + " Agg :" + agg)
    if port == "":
        try:
            write_api.write(bucket, org, [{"measurement": "support_switch_loop.py", "tags": {"IP_Address": ipadd, "AggId": agg}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass 
        syslog.syslog(syslog.LOG_INFO, "Executing function check_save")
        save_resp = check_save(ipadd, agg, "loop")
        if save_resp == "0":
            syslog.syslog(syslog.LOG_INFO, "No decision saved")
            notif = "A network loop has been detected on your network on the linkagg {} - System Description: N/A - OmniSwitch {}/{}.\nIf you click on Yes, the following actions will be done: Port Admin Down.".format(agg, ipadd, hostname)
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Rainbow Adaptive Card")
            answer = send_message_request(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            if answer == "2":
                syslog.syslog(syslog.LOG_INFO, "Executing function add_new_save")
                add_new_save(ipadd, agg, "loop", choice="always")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Agg: " + agg + " Choice: " + " Always")
                answer = '1'
            elif answer == "0":
                syslog.syslog(syslog.LOG_INFO, "Executing function add_new_save")
                add_new_save(ipadd, agg, "loop", choice="never")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Agg: " + agg + " Choice: " + " Never")

        elif save_resp == "-1":
            print("Decision saved to No - script exit")
            syslog.syslog(syslog.LOG_INFO, "Decision saved to No - script exit")
            sys.exit()
        else:
            answer = '1'
            syslog.syslog(syslog.LOG_INFO, "No answer - Decision set to Yes - Script exit - will be called by next occurence")    

        syslog.syslog(syslog.LOG_INFO, "Rainbow Acaptive Card answer: " + answer)


    else:

        try:
            write_api.write(bucket, org, [{"measurement": "support_switch_loop.py", "tags": {"IP_Address": ipadd, "Port": port}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
        # We cannot do SSH on switch when entering into Network Loop 
        #syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_lldp_port_description")
        #lldp_port_description, _ = collect_command_output_lldp_port_description(switch_user, switch_password, port, ip)
        syslog.syslog(syslog.LOG_INFO, "Executing function check_save")
        save_resp = check_save(ipadd, port, "loop")
        if save_resp == "0":
            syslog.syslog(syslog.LOG_INFO, "No decision saved")
            notif = "A network loop has been detected on your network port {} - on OmniSwitch {}/{}.\nIf you click on Yes, the following actions will be done: Port Admin Down.".format(port, ipadd, hostname)
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Calling VNA API - Rainbow Adaptive Card")
            answer = send_message_request(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

            if answer == "2":
                add_new_save(ipadd, port, "loop", choice="always")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Port: " + port + " Choice: " + " Always")
 
                answer = '1'
            elif answer == "0":
                add_new_save(ipadd, port, "loop", choice="never")
                syslog.syslog(syslog.LOG_INFO, "Add new save function - IP Address: " + ipadd + " Port: " + port + " Choice: " + " Never")
 
        elif save_resp == "-1":
            print("Decision saved to No - script exit")
            syslog.syslog(syslog.LOG_INFO, "Decision saved to No - script exit")
            sys.exit()
        else:
            answer = '1'
            syslog.syslog(syslog.LOG_INFO, "No answer - Decision set to Yes - Script exit - will be called by next occurence")    

        syslog.syslog(syslog.LOG_INFO, "Rainbow Acaptive Card answer: " + answer)

    if answer == '1':
        if port == "":
            syslog.syslog(syslog.LOG_INFO, "Anwser received is Yes - Network Loop detected on LinkAgg")
            cmd = "linkagg lacp agg " + agg + " admin-state disable"
            syslog.syslog(syslog.LOG_INFO, "Linkagg disable on agg {} {} {}".format(agg, ipadd, hostname))
            ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
            syslog.syslog(syslog.LOG_INFO, "LinkAgg is administratively disabled")
        else:
            syslog.syslog(syslog.LOG_INFO, "Anwser received is Yes - Network Loop detected on Normal Port")
            cmd = "interface port " + port + " admin-state disable"
            syslog.syslog(syslog.LOG_INFO, "Port disable on port {} {} {}".format(port, ipadd, hostname))
            ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
            syslog.syslog(syslog.LOG_INFO, "Port is administratively disabled")
        syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_network_loop")       
        filename_path, subject, action, result, category = collect_command_output_network_loop(switch_user, switch_password, ipadd, port)
        syslog.syslog(syslog.LOG_INFO, "Subject: " + subject)
        syslog.syslog(syslog.LOG_INFO, "Action: " + action)
        syslog.syslog(syslog.LOG_INFO, "Result: " + result)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Send File")      
        send_file(filename_path, subject, action, result, category, jid)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        # disable_debugging
        appid = "slNi"
        subapp = "20"
        level = "info"
        syslog.syslog(syslog.LOG_INFO, "Executing function debugging - swlog appid slNi subapp 20 level info")
        debugging(switch_user, switch_password,ipadd, appid, subapp, level)
        sleep(2)


counter = 0
last_time = ""
last_ip = ""
last_port = ""
last_mac = ""
text_file = ""
last_agg = ""

with open("/var/log/devices/lastlog_loop.json", "r", errors='ignore') as log_file:
    lines = log_file.readlines()
    for line in reversed(lines):
        try:
            line_json = json.loads(line)
            timestamp = (str(line_json["@timestamp"])[:19]).replace("T", " ").replace(":", " ").replace("-", " ")
            time = datetime.strptime(timestamp, "%Y %m %d %H %M %S")
            if counter == 0:
                last_time = time
                last_ip = line_json["relayip"]
                last_hostname = line_json["hostname"]
                msg = line_json["message"]
                syslog.syslog(syslog.LOG_DEBUG, "Syslog Last IP Address: " + last_ip)
                syslog.syslog(syslog.LOG_DEBUG, "Syslog Last Hostname: " + last_hostname)
                if "aggId" in msg:
                    last_mac = re.findall(r"(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))", msg)[0][0]
                    last_agg = re.findall(r"aggId: (\d*)", msg)[0]
                    syslog.syslog(syslog.LOG_DEBUG, "Syslog Last MAC Address: " + last_mac)
                    syslog.syslog(syslog.LOG_DEBUG, "Syslog Last Aggregate ID: " + last_agg)
                    counter = 1
                else:
                    last_port = str(re.findall(r"(\d*/\d*/\d*)", msg)[0]).replace("\\", "")
                    syslog.syslog(syslog.LOG_DEBUG, "Syslog Last Port: " + last_port)
                    counter = 1
                text_file = line
            elif time > (last_time - timedelta(seconds=10)): # reducing the file to a 10 sec window
                text_file = line + text_file
            else:
                break
                
        except json.decoder.JSONDecodeError:
            print("File /var/log/devices/lastlog_loop.json empty")
            syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_loop.json - JSONDecodeError")
            exit()
        except IndexError:
            syslog.syslog(syslog.LOG_INFO, "Index error in regex")
            pass

with open("/var/log/devices/lastlog_loop.json", "w", errors='ignore') as log_file:
    log_file.write(text_file)

counter = 0
function = "loop"
#### Put back timer to 5 minutes as per last feedback from James
if script_has_run_recently(300, last_ip,function):
    print('Executing script exit because executed within 300 seconds time period')
    syslog.syslog(syslog.LOG_DEBUG, "Executing script exit because executed within 300 seconds time period")
    exit()

with open("/var/log/devices/lastlog_loop.json", "r", errors='ignore') as log_file:
    for line in log_file:
        try:
            log_json = json.loads(line)
            ipadd = log_json["relayip"]
            hostname = log_json["hostname"]
            msg = log_json["message"]
            port = "null"
            agg = "null"
            syslog.syslog(syslog.LOG_DEBUG, "Syslog IP Address: " + ipadd)
            syslog.syslog(syslog.LOG_DEBUG, "Syslog Hostname: " + hostname)

            if ipadd == last_ip:
                if "aggId" in msg:
                    syslog.syslog(syslog.LOG_DEBUG, "IP Address same as Last IP Address and port is member of a LinkAgg")
                    agg = re.findall(r"aggId: (\d*)", msg)[0]
                elif last_mac != "" : # line is a normal port, we check if moving MAC correspond
                    syslog.syslog(syslog.LOG_DEBUG, "IP Address same as Last IP Address and port is not member of a LinkAgg")
                    mac = re.findall(r"(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))", msg)[0][0]
                    if mac == last_mac:
                        syslog.syslog(syslog.LOG_DEBUG, "MAC Address same as Last MAC Address")
                        last_port = str(re.findall(r"(\d*/\d*/\d*)", msg)[0]).replace("\\", "")
                        last_mac = ""
                else:
                    syslog.syslog(syslog.LOG_DEBUG, "IP Address same as Last IP Address and port is not member of a LinkAgg")
                    port = str(re.findall(r"(\d*/\d*/\d*)", msg)[0]).replace("\\", "")

                print("log: {}".format(ipadd))
        except json.decoder.JSONDecodeError:
            print("File /var/log/devices/lastlog_loop.json empty")
            syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_loop.json - JSONDecodeError")
            exit()
        except IndexError:
            syslog.syslog(syslog.LOG_INFO, "Index error in regex")
            pass

        if port == last_port or agg == last_agg:
            syslog.syslog(syslog.LOG_DEBUG, "Port same as Last Port and Aggregate same as Last Aggregate - we increment the counter")
            counter += 1
            print(counter)
            
        if(counter == 10): # Number of occurences needed to trigger
            syslog.syslog(syslog.LOG_DEBUG, "We have 10 occurences we are executing the function process")
            process(ipadd, hostname, last_port, last_agg)
            break