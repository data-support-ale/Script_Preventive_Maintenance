#!/usr/local/bin/python3.7
from asyncio.subprocess import PIPE, STDOUT
from copy import error
from pickle import NONE
import sys
import os
import logging
import datetime
from time import sleep
from unicodedata import name

from support_send_notification import *
import subprocess
import re
import requests
import paramiko
from database_conf import *
import syslog

syslog.openlog('support_tools_Stellar')
# This script contains all functions interacting with WLAN Stellar APs

# Function for extracting environment information from ALE_script.conf file


def get_credentials(attribute=None):
    """ 
    This function collects all the information about the switch's credentials in the log. 
    It collects also the information usefull for  notification sender in the file ALE_script.conf.

    :param:                         None
    :return str user:               Switch user login
    :return str password:           Switch user password
    :return str jid:                 Rainbow JID  of recipients
    :return str gmail_usr:          Sender's email userID
    :return str gmail_passwd:       Sender's email password               
    :return str mails:              List of email addresses of recipients
    """

    with open("/opt/ALE_Script/ALE_script.conf", "r") as content_variable:
        login_switch, pass_switch, mails, rainbow_jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company, room_id, * \
            kargs = re.findall(
                r"(?:,|\n|^)(\"(?:(?:\"\")*[^\"]*)*\"|[^\",\n]*|(?:\n|$))", str(content_variable.read()))
        if attribute == None:
            return login_switch, pass_switch, mails, rainbow_jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company
        elif attribute == "login_switch":
            return login_switch
        elif attribute == "pass_switch":
            return pass_switch
        elif attribute == "mails":
            return mails
        elif attribute == "rainbow_jid":
            return rainbow_jid
        elif attribute == "ip_server":
            return ip_server
        elif attribute == "login_AP":
            return login_AP
        elif attribute == "pass_AP":
            return pass_AP
        elif attribute == "tech_pass":
            return tech_pass
        elif attribute == "random_id":
            return random_id
        elif attribute == "company":
            return company
        elif attribute == "room_id":
            return room_id

login_switch, pass_switch, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

# Function SSH for checking connectivity before collecting logs
def ssh_connectivity_check(login_AP, pass_AP, ipadd, cmd):
    """ 
    This function takes entry the command to push remotely on WLAN Stellar AP by SSH with support account with Python Paramiko module
    Paramiko exceptions are handled for notifying Network Administrator if the SSH Session does not establish

    :param str cmd                  Command pushed by SSH on WLAN Stellar AP
    :param str ipadd                Stellar IP address
    :return:  stdout, stderr        If exceptions is returned on stderr a notification is sent to Network Administrator, else we log the session was established
    """
    exception = output = 0
    print("Function ssh_connectivity_check - we execute command " + cmd + " on Device: " + ipadd)
    syslog.syslog(syslog.LOG_INFO, "Function ssh_connectivity_check - we execute command " + cmd + " on Device " + ipadd)
    cmd = str(cmd)
    try:
        p = paramiko.SSHClient()
        p.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        syslog.syslog(syslog.LOG_INFO, "SSH Session start")
        p.connect(ipadd, port=22, username=login_AP,password=pass_AP, timeout=60.0, banner_timeout=200)
        syslog.syslog(syslog.LOG_INFO, "SSH Session established")
    except TimeoutError as exception:
        exception = "SSH Timeout"
        syslog.syslog(syslog.LOG_INFO, "Exception: " + str(exception))
        print("Function ssh_connectivity_check - Exception: " + str(exception))
        print("Function ssh_connectivity_check - Timeout when establishing SSH Session")
        notif = ("Timeout when establishing SSH Session to WLAN Stellar AP {0}, we cannot collect logs").format(ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message(notif, jid)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "Timed out", "IP_Address": ipadd}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as exception:
            print(exception)
        except Exception as exception:
            print(exception)
        syslog.syslog(syslog.LOG_INFO, "Script exit")
        os._exit(1)
    except paramiko.AuthenticationException:
        exception = "AuthenticationException"
        syslog.syslog(syslog.LOG_INFO, "Exception: " + str(exception))
        print("Function ssh_connectivity_check - Authentication failed enter valid user name and password")
        notif = ("SSH Authentication failed when connecting to WLAN Stellar AP {0}, we cannot collect logs or proceed for remediation action").format(ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message(notif, jid)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "AuthenticationException", "IP_Address": ipadd}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as exception:
            print(exception)
            return exception 
        except Exception as exception:
            print(exception)
            return exception 
        syslog.syslog(syslog.LOG_INFO, "Script exit")
        os._exit(1)
    except (paramiko.SSHException,ConnectionError) as exception:
        syslog.syslog(syslog.LOG_INFO, "Exception: " + str(exception))
        print("Function ssh_connectivity_check - " + str(exception))
        #exception = exception.readlines()
        exception = str(exception)
        print("Function ssh_connectivity_check - Device unreachable")
        syslog.syslog(syslog.LOG_INFO, " SSH session does not establish on WLAN Stellar AP " + ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        notif = ("WLAN Stellar AP {0} is unreachable, we cannot collect logs").format(ipadd)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message(notif, jid)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "DeviceUnreachable", "IP_Address": ipadd}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as exception:
            print(exception)
            return exception
        except Exception as exception:
            print(exception)
            return exception
        syslog.syslog(syslog.LOG_INFO, "Script exit")
        os._exit(1)
    except Exception as exception:
        syslog.syslog(syslog.LOG_INFO, "Exception: " + str(exception))
        print("Function ssh_connectivity_check - " + str(exception))
        #exception = exception.readlines()
        exception = str(exception)
        print("Function ssh_connectivity_check - Device unreachable")
        logging.info(' SSH session does not establish on WLAN Stellar AP ' + ipadd)
        notif = ("WLAN Stellar AP {0} is unreachable, we cannot collect logs").format(ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)        
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message(notif, jid)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "DeviceUnreachable", "IP_Address": ipadd}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as exception:
            print(exception)
            return exception
        except Exception as exception:
            print(exception)
            return exception
        syslog.syslog(syslog.LOG_INFO, "Script exit")
        os._exit(1)
    try:
        stderr = ""
        stdout = ""
        stdin = ""
        syslog.syslog(syslog.LOG_INFO, "SSH Command Execution: " + cmd)
        stdin, stdout, stderr = p.exec_command(cmd, timeout=120)
        #stdin, stdout, stderr = threading.Thread(target=p.exec_command,args=(cmd,))
        # stdout.start()
        # stdout.join(1200)
    except TypeError as exception:
        pass
    except paramiko.SSHException as exception:
        print(str(exception))
        syslog.syslog(syslog.LOG_INFO, "Exception: " + str(exception))
        pass
    try:
        exception = stderr.readlines()
        exception = str(exception)
        connection_status = stdout.channel.recv_exit_status()
    except:
        connection_status = 1
    print(connection_status)
    print(exception)
    if connection_status != 0:
        notif = ("The python script execution on WLAN Stellar AP {0} failed - {1}").format(ipadd, exception)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message(notif, jid)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass
        os._exit(1) 
    else:
        notif = ("SSH Session established successfully on WLAN Stellar AP {0}").format(ipadd)
        syslog.syslog(syslog.LOG_INFO, "SSH Session established successfully on WLAN Stellar AP " + ipadd +  " and command " + cmd + " passed")
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_success", "tags": {"IP_Address": ipadd}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        output = stdout.readlines()
        # We close SSH Session once retrieved command output
        p.close()
        syslog.syslog(syslog.LOG_INFO, "SSH Session End")
        return output

def  drm_neighbor_scanning(login_AP, pass_AP, neighbor_ip):
    """ 
    This function returns the neighbor channel scanned and current channel set on WLAN Stellar AP

    :param str login_AP:                   WLAN Stellar AP support login
    :param str pass_AP:                    WLAN Stellar AP support password
    :param str neighbor_ip:                WLAN Stellar Neighbor IP Address when scanning
    :return:                               filename_path,subject,action,result,category
    """
    syslog.syslog(syslog.LOG_INFO, "Executing function drm_neighbor_scanning")
    l_stellar_cmd = []
    l_stellar_cmd.append("echo -e \"\n Collecting tech_support_command 13 output: \n\"; ssudo tech_support_command 13")
    for stellar_cmd in l_stellar_cmd:
            #cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(pass_AP, login_AP, neighbor_ip, stellar_cmd)
            output = ssh_connectivity_check(login_AP, pass_AP, neighbor_ip, stellar_cmd)
            #output = subprocess.check_output(cmd, stderr=PIPE, timeout=40, shell=True)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
            else:
                exception = "Timeout"
                notif = ("Timeout when establishing SSH Session to WLAN Stellar AP {0}, we cannot collect logs").format(neighbor_ip)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message(notif, jid)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")

                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": neighbor_ip, "Exception": exception}, "fields": {"count": 1}}])
                    syslog.syslog(syslog.LOG_INFO, "Statistics saved")
                except UnboundLocalError as error:
                    print(str(error))
                except Exception as error:
                    print(str(error))
                    pass 
                os._exit(1)
    print(output_decode)
    if "Channel" in output_decode:
        try:
            my_channel = re.findall(r"    Channel:(.*)", output_decode)
            print(my_channel)
        except IndexError:
            print("Index error in regex")
            syslog.syslog(syslog.LOG_INFO, "Index error in regex for my_channel")
            os._exit(1)
    return my_channel

def  channel_utilization_per_band(login_AP, pass_AP, ipadd, channel_utilization):
    """ 
    This function returns the neighbor channel scanned and current channel set on WLAN Stellar AP

    :param str login_AP:                   WLAN Stellar AP support login
    :param str pass_AP:                    WLAN Stellar AP support password
    :param str channel_utilization:        WLAN Stellar AP channel utilization
    :return:                               filename_path,subject,action,result,category, channel, band
    """
    syslog.syslog(syslog.LOG_INFO, "Executing function channel_utilization_per_band")
    l_stellar_cmd = []
    l_stellar_cmd.append("echo -e \"\n Collecting tech_support_command 13 output: \n\"; ssudo tech_support_command 13")
    for stellar_cmd in l_stellar_cmd:
        #cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(pass_AP, login_AP, ipadd, stellar_cmd)
            output = ssh_connectivity_check(login_AP, pass_AP, ipadd, stellar_cmd)
            #output = subprocess.check_output(cmd, stderr=PIPE, timeout=40, shell=True)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
            else:
                exception = "Timeout"
                notif = ("Timeout when establishing SSH Session to WLAN Stellar AP {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message(notif, jid)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                    syslog.syslog(syslog.LOG_INFO, "Statistics saved")
                except UnboundLocalError as error:
                    print(str(error))
                except Exception as error:
                    print(str(error))
                    pass 
                os._exit(1)
    print(output_decode)
    if "Channel" in output_decode:
        try:
            channel = re.findall(r"    Channel:(.*)", output_decode)
            print(channel)
        except IndexError:
            print("Index error in regex")
            syslog.syslog(syslog.LOG_INFO, "Index error in regex for channel")
            pass  
    if "Utilization" in output_decode:
        try:
            utilization = re.findall(r"    Utilization:(.*)", output_decode)
            print(utilization)
        except IndexError:
            print("Index error in regex")
            syslog.syslog(syslog.LOG_INFO, "Index error in regex for utilization")
            pass  
    return channel

def sta_limit_reached_tools(login_AP, pass_AP, ipadd):
    """ 
    This function returns file path containing the tech_support command outputs and the notification subject, body used when calling VNA API

    :param str login_AP:                   WLAN Stellar AP support login
    :param str pass_AP:                    WLAN Stellar AP support password
    :param str ipadd:                      WLAN Stellar AP IP address
    :return:                               filename_path,subject,action,result,category
    """
    syslog.syslog(syslog.LOG_INFO, "Executing function sta_limit_reached_tools")
    text = "More logs about the WLAN Stellar AP : {0} \n\n\n".format(ipadd)

    l_stellar_cmd = []
    l_stellar_cmd.append("echo -e \"\n Collecting tech_support_command 1 output: \n\"; ssudo tech_support_command 1; \
       echo -e \"\n Collecting tech_support_command 2 output: \n\"; ssudo tech_support_command 2; \
       echo -e \"\n Collecting tech_support_command 4 output: \n\"; ssudo tech_support_command 4; \
       echo -e \"\n Collecting tech_support_command 10 output: \n\"; ssudo tech_support_command 10; \
       echo -e \"\n Collecting tech_support_command 13 output: \n\"; ssudo tech_support_command 13; \
       echo -e \"\n Collecting tech_support_command 16 output: \n\"; ssudo tech_support_command 16; \
       echo -e \"\n Collecting tech_support_command 19 output: \n\"; ssudo tech_support_command 19; \
       echo -e \"\n Collecting tech_support_command 21 output: \n\"; ssudo tech_support_command 21; \
       echo -e \"\n Collecting tech_support_command 27 output: \n\"; ssudo tech_support_command 27")
    l_stellar_cmd.append("echo -e \"\n Collecting WLAN Stellar AP Snapshot logs thru TFTP \n\";ssudo tech_support_command 12 " + ip_server)

    for stellar_cmd in l_stellar_cmd:
        cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(pass_AP, login_AP, ipadd, stellar_cmd)
        try:
            stderr = ""
            output = ssh_connectivity_check(login_AP, pass_AP, ipadd, stellar_cmd)
            #output = subprocess.check_output(cmd, stderr=PIPE, timeout=40, shell=True)
            print(stderr)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
                text = "{0}{1}: \n{2}\n\n".format(text, stellar_cmd, output_decode)
            else:
                exception = "Timeout"
                notif = ("Timeout when establishing SSH Session to WLAN Stellar AP {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message(notif, jid)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                    syslog.syslog(syslog.LOG_INFO, "Statistics saved")
                except UnboundLocalError as error:
                    print(str(error))
                except Exception as error:
                    print(str(error))
                    pass 
                os._exit(1)
        except subprocess.TimeoutExpired as exception:
            notif = ("The python script execution on WLAN Stellar AP {0} failed - {1}").format(ipadd, exception)
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
            send_message(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            except UnboundLocalError as error:
                print(str(error))
            except Exception as error:
                print(str(error))
                pass 
            os._exit(1)
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_sta_limit_reached_logs".format(
        date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = ('/opt/ALE_Script/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - The number of associated WLAN Clients to BSSID on WLAN Stellar AP {0} reached the limit").format(ipadd)
    action = "Attached to this notification the command outputs, please check if the number of associated clients corresponds to the maximum number of clients allowed per band (default: 64) "
    result = ("WLAN Stellar AP snapshot logs are collected and stored on /tftpboot/ directory on server {0}. If you observe disprecancies between the number of clients associated versus number of clients allowed please contact ALE Customer Support").format(ip_server)
    category = "sta_limit"
    return filename_path, subject, action, result, category

def vlan_limit_reached_tools(login_AP, pass_AP, ipadd):
    """ 
    This function returns file path containing the tech_support command outputs and the notification subject, body used when calling VNA API

    :param str login_AP:                   WLAN Stellar AP support login
    :param str pass_AP:                    WLAN Stellar AP support password
    :param str ipadd:                      WLAN Stellar AP IP address
    :return:                               filename_path,subject,action,result,category
    """
    syslog.syslog(syslog.LOG_INFO, "Executing function vlan_limit_reached_tools")
    text = "More logs about the WLAN Stellar AP : {0} \n\n\n".format(ipadd)

    l_stellar_cmd = []
    l_stellar_cmd.append("echo -e \"\n Collecting tech_support_command 1 output: \n\"; ssudo tech_support_command 1; \
       echo -e \"\n Collecting tech_support_command 2 output: \n\"; ssudo tech_support_command 2; \
       echo -e \"\n Collecting tech_support_command 4 output: \n\"; ssudo tech_support_command 4; \
       echo -e \"\n Collecting tech_support_command 10 output: \n\"; ssudo tech_support_command 10; \
       echo -e \"\n Collecting tech_support_command 13 output: \n\"; ssudo tech_support_command 13; \
       echo -e \"\n Collecting tech_support_command 16 output: \n\"; ssudo tech_support_command 16; \
       echo -e \"\n Collecting tech_support_command 19 output: \n\"; ssudo tech_support_command 19; \
       echo -e \"\n Collecting tech_support_command 21 output: \n\"; ssudo tech_support_command 21; \
       echo -e \"\n Collecting tech_support_command 27 output: \n\"; ssudo tech_support_command 27; \
       echo -e \"\n Collecting Access Role Profile config file: \n\"; cat /var/config/access_role.conf")
    l_stellar_cmd.append("echo -e \"\n Collecting WLAN Stellar AP Snapshot logs thru TFTP \n\";ssudo tech_support_command 12 " + ip_server)
    for stellar_cmd in l_stellar_cmd:
        cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(pass_AP, login_AP, ipadd, stellar_cmd)
        try:
            output = ssh_connectivity_check(login_AP, pass_AP, ipadd, stellar_cmd)
            #output = subprocess.check_output(cmd, stderr=PIPE, timeout=40, shell=True)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
                text = "{0}{1}: \n{2}\n\n".format(text, stellar_cmd, output_decode)
            else:
                exception = "Timeout"
                notif = ("Timeout when establishing SSH Session to WLAN Stellar AP {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message(notif, jid)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                    syslog.syslog(syslog.LOG_INFO, "Statistics saved")
                except UnboundLocalError as error:
                    print(str(error))
                except Exception as error:
                    print(str(error))
                    pass 
                os._exit(1)
        except subprocess.TimeoutExpired as exception:
            notif = ("The python script execution on WLAN Stellar AP {0} failed - {1}").format(ipadd, exception)
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
            send_message(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            except UnboundLocalError as error:
                print(str(error))
            except Exception as error:
                print(str(error))
                pass 
            os._exit(1)
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_vlan_limit_reached_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = ('/opt/ALE_Script/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - The number of created VLAN reached the limit on WLAN Stellar AP {0}").format(ipadd)
    action = "Depending of the WLAN Stellar AP model, the VLAN count differs. AP1101/AP1201H(L) (4 VLANs), AP1201 (16 VLANs), others models (32 VLANs)"
    result = ("WLAN Stellar AP snapshot logs are collected and stored on /tftpboot/ directory on server {0}. If you observe disprecancies between the number of VLAN created versus number of VLAN allowed on your WLAN Stellar AP model, please contact ALE Customer Support").format(ip_server)
    category = "vlan_limit"
    return filename_path, subject, action, result, category

def collect_logs(login_AP, pass_AP, ipadd, pattern):
    """ 
    This function collect snapshot logs and additionnal logs on Stellar AP when specific pattern is noticed

    :param str login_AP:                   WLAN Stellar AP support login
    :param str pass_AP:                    WLAN Stellar AP support password
    :param str ipadd:                      WLAN Stellar AP IP address
    :return:                               filename_path,subject,action,result,category
    """
    syslog.syslog(syslog.LOG_INFO, "Executing function WLAN collect_logs")
    text = "More logs about the WLAN Stellar AP : {0} \n\n\n".format(ipadd)

    l_stellar_cmd = []
    l_stellar_cmd.append("echo -e \"\n Collecting tech_support_command 1 output: \n\"; ssudo tech_support_command 1; \
       echo -e \"\n Collecting tech_support_command 2 output: \n\"; ssudo tech_support_command 2; \
       echo -e \"\n Collecting tech_support_command 4 output: \n\"; ssudo tech_support_command 4; \
       echo -e \"\n Collecting tech_support_command 10 output: \n\"; ssudo tech_support_command 10; \
       echo -e \"\n Collecting tech_support_command 13 output: \n\"; ssudo tech_support_command 13; \
       echo -e \"\n Collecting tech_support_command 16 output: \n\"; ssudo tech_support_command 16; \
       echo -e \"\n Collecting tech_support_command 19 output: \n\"; ssudo tech_support_command 19; \
       echo -e \"\n Collecting tech_support_command 21 output: \n\"; ssudo tech_support_command 21; \
       echo -e \"\n Collecting tech_support_command 27 output: \n\"; ssudo tech_support_command 27")
    l_stellar_cmd.append("echo -e \"\n Collecting WLAN Stellar AP Snapshot logs thru TFTP \n\";ssudo tech_support_command 12 " + ip_server)
    for stellar_cmd in l_stellar_cmd:
        try:
            output = ssh_connectivity_check(login_AP, pass_AP, ipadd, stellar_cmd)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
                text = "{0}{1}: \n{2}\n\n".format(text, stellar_cmd, output_decode)
            else:
                exception = "Timeout"
                notif = ("Timeout when establishing SSH Session to WLAN Stellar AP {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message(notif, jid)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                    syslog.syslog(syslog.LOG_INFO, "Statistics saved")
                except UnboundLocalError as error:
                    print(str(error))
                except Exception as error:
                    print(str(error))
                    pass 
                os._exit(1)
        except (subprocess.TimeoutExpired,subprocess.SubprocessError) as exception:
            notif = ("The python script execution on WLAN Stellar AP {0} failed - {1}").format(ipadd, exception)
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
            send_message(notif, jid)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                syslog.syslog(syslog.LOG_INFO, "Statistics saved")
            except UnboundLocalError as error:
                print(str(error))
            except Exception as error:
                print(str(error))
                pass 
            os._exit(1)
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_snapshot_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = ('/opt/ALE_Script/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - The following pattern \"{0}\" is noticed on WLAN Stellar AP {1}").format(pattern,ipadd)
    action = ("A Pattern \"{0}\" has been detected in WLAN Stellar AP syslogs (IP Address : {1}). A WLAN Stellar AP snapshot log is collected and stored in the server: {2}, directory : /tftpboot/").format(pattern, ipadd, ip_server)
    result = "Find attached to this notification additionnal logs"
    category = "pattern"
    return filename_path, subject, action, result, category


if __name__ == "__main__":
    jid = "570e12872d768e9b52a8b975@openrainbow.com"
    pass_AP = "Letacla01*"
    login_AP = "support"
    ipadd = "10.130.7.11"
    cmd = "/usr/sbin/showsysinfo"
    host = "StellarAP1361"
    #pass_root = ssh_connectivity_check(login_AP, pass_AP, ipadd, cmd)
    filename_path, subject, action, result, category = sta_limit_reached_tools(login_AP, pass_AP, ipadd)
    send_file(filename_path, subject, action, result, category, jid)
    filename_path, subject, action, result, category = vlan_limit_reached_tools(login_AP, pass_AP, ipadd)
    send_file(filename_path, subject, action, result, category, jid)

else:
    print("Support_Tools_Stellar Script called by another script")