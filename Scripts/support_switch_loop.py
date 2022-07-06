#!/usr/local/bin/python3.7
import sys
import json
import syslog

from prometheus_client import Histogram
from support_tools_OmniSwitch import debugging, get_credentials, collect_command_output_lldp_port_description, add_new_save, check_save, ssh_connectivity_check, script_has_run_recently
from time import strftime, localtime, sleep
from datetime import datetime, timedelta
import re
from support_send_notification import send_message, send_message_request
from database_conf import *


def process(ip, hostname, port, agg):
    syslog.syslog(syslog.LOG_DEBUG, "Process called with: " + " ip :" + ip + " hostname :" + hostname + " port :" + port + " agg :" + agg)
    if port == "":
        try:
            write_api.write(bucket, org, [{"measurement": "support_switch_loop.py", "tags": {
                                "IP_Address": ip, "AggId": agg}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass 

        save_resp = check_save(ip, agg, "loop")
        if save_resp == "0":
            info = "A network loop has been detected on your network on the linkagg {} - System Description: N/A - OmniSwitch {}/{}.\nIf you click on Yes, the following actions will be done: Port Admin Down.".format(
                agg, ip, hostname)
            answer = send_message_request(info, jid)
            if answer == "2":
                add_new_save(ip, agg, "loop", choice="always")
                answer = '1'
            elif answer == "0":
                add_new_save(ip, agg, "loop", choice="never")
        elif save_resp == "-1":
            sys.exit()
        else:
            answer = '1'

    else:

        try:
            write_api.write(bucket, org, [{"measurement": "support_switch_loop.py", "tags": {
                            "IP_Address": ip, "Port": port}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass 

        lldp_port_description, _ = collect_command_output_lldp_port_description(switch_user, switch_password, port, ip)

        save_resp = check_save(ip, port, "loop")
        if save_resp == "0":
            info = "A network loop has been detected on your network on the access port {} - System Description: {} - OmniSwitch {}/{}.\nIf you click on Yes, the following actions will be done: Port Admin Down.".format(
                port, lldp_port_description, ip, hostname)
            answer = send_message_request(info, jid)
            if answer == "2":
                add_new_save(ip, port, "loop", choice="always")
                answer = '1'
            elif answer == "0":
                add_new_save(ip, port, "loop", choice="never")
        elif save_resp == "-1":
            sys.exit()
        else:
            answer = '1'

    if answer == '1':
        if port == "":
            cmd = "linkagg lacp agg " + agg + " admin-state disable"
            syslog.syslog(syslog.LOG_INFO, "Linkagg disable on agg {} {} {}".format(agg, ip, hostname))
            ssh_connectivity_check(switch_user, switch_password, ip, cmd)
            os.system(
                'logger -t montag -p user.info AggId {0} of OmniSwitch {1}/{2} updated'.format(port, agg, hostname))
            os.system('logger -t montag -p user.info Process terminated')
            info = "Preventive Maintenance Application - A network loop has been detected on your network and the linkagg {0} is administratively down on OmniSwitch {1}/{2}".format(agg, ip, hostname)
        else:
            cmd = "interface port " + port + " admin-state disable"
            syslog.syslog(syslog.LOG_INFO, "Port disable on port {} {} {}".format(port, ip, hostname))
            ssh_connectivity_check(switch_user, switch_password, ip, cmd)
            os.system(
                'logger -t montag -p user.info Port {0} of OmniSwitch {1}/{2} updated'.format(port, port, hostname))
            os.system('logger -t montag -p user.info Process terminated')
            info = "Preventive Maintenance Application - A network loop has been detected on your network and the port {0} is administratively down on OmniSwitch {1}/{2}".format(port, ip, hostname)

        send_message(info, jid)
        # disable_debugging
        ipadd = ip
        appid = "bcmd"
        subapp = "all"
        level = "info"
        debugging(switch_user, switch_password,
                ipadd, appid, subapp, level)
        sleep(2)

# Script init
script_name = sys.argv[0]
#os.system('logger -t montag -p user.info Executing script :' + script_name)
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

syslog.openlog('support_switch_loop')
syslog.syslog(syslog.LOG_INFO, "Executing script")

# Get informations from logs.
switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()
subject = "A network loop was detected in your network !"

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
                if "aggId" in msg:
                    last_mac = re.findall(r"(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))", msg)[0][0]
                    last_agg = re.findall(r"aggId: (\d*)", msg)[0]
                    counter = 1
                else:
                    last_port = str(re.findall(r"(\d*/\d*/\d*)", msg)[0]).replace("\\", "")
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
            pass

with open("/var/log/devices/lastlog_loop.json", "w", errors='ignore') as log_file:
    log_file.write(text_file)


syslog.syslog(syslog.LOG_DEBUG, "Syslog IP Address: " + last_ip)
syslog.syslog(syslog.LOG_DEBUG, "Syslog Hostname: " + last_hostname)
syslog.syslog(syslog.LOG_DEBUG, "Syslog port: " + last_port)
syslog.syslog(syslog.LOG_DEBUG, "Syslog agg: " + last_agg)

counter = 0
function = "loop"
if script_has_run_recently(30, last_ip,function):
    print('you need to wait before you can run this again')
    syslog.syslog(syslog.LOG_DEBUG, "Executing script exit because executed within 30 sec time period")
    os.system('logger -t montag -p user.info Executing script exit because executed within 30 sec time period')
    exit()

with open("/var/log/devices/lastlog_loop.json", "r", errors='ignore') as log_file:
    for line in log_file:
        try:
            log_json = json.loads(line)
            ip = log_json["relayip"]
            hostname = log_json["hostname"]
            msg = log_json["message"]
            port = "null"
            agg = "null"
            if ip == last_ip:
                if "aggId" in msg:
                    agg = re.findall(r"aggId: (\d*)", msg)[0]
                elif last_mac != "" : # line is a normal port, we check if moving MAC correspond
                    mac = re.findall(r"(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))", msg)[0][0]
                    if mac == last_mac:
                        last_port = str(re.findall(r"(\d*/\d*/\d*)", msg)[0]).replace("\\", "")
                        last_mac = ""
                else:
                    port = str(re.findall(r"(\d*/\d*/\d*)", msg)[0]).replace("\\", "")

                print("log: {}".format(ip))
        except json.decoder.JSONDecodeError:
            print("File /var/log/devices/lastlog_loop.json empty")
            syslog.syslog(syslog.LOG_INFO, "File /var/log/devices/lastlog_loop.json - JSONDecodeError")
            exit()
        except IndexError:
            pass

        if port == last_port or agg == last_agg:
            counter += 1
            print(counter)
            
        if(counter == 10): # Number of occurences needed to trigger
            process(ip, hostname, last_port, last_agg)
            break