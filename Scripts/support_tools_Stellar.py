#!/usr/local/bin/python3.7

from asyncio.subprocess import PIPE
from copy import error
import sys
import os
import logging
import datetime
from time import sleep
from unicodedata import name

from paramiko import SSHException
from support_send_notification import send_message, send_file
import subprocess
import re
import pysftp
import requests
import paramiko
import csv
import threading
from database_conf import *

# This script contains all functions interacting with Stellar APs

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
    This function takes entry the command to push remotely on Stellar AP by SSH with support account with Python Paramiko module
    Paramiko exceptions are handled for notifying Network Administrator if the SSH Session does not establish

    :param str cmd                  Command pushed by SSH on Stellar AP
    :param str ipadd                    Stellar IP address
    :return:  stdout, stderr          If exceptions is returned on stderr a notification is sent to Network Administrator, else we log the session was established
    """
    print(cmd)
    try:
        p = paramiko.SSHClient()
        p.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        p.connect(ipadd, port=22, username=login_AP,
                  password=pass_AP, timeout=60.0, banner_timeout=200)
    except ConnectionError as exception:
        print(exception)
        print("SSH not allowed when establishing SSH Session")
        info = (
            "SSH Connection fails when establishing SSH Session to Stellar AP {0}, please verify if SSH is enabled on the AP Group").format(ipadd)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                        "Reason": "Timed out", "IP_Address": ipadd}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit(0)
        except Exception as error:
            print(error)
            pass
    except TimeoutError as exception:
        print(exception)
        print("Timeout when establishing SSH Session")
        info = (
            "Timeout when establishing SSH Session to Stellar AP {0}, we cannot collect logs").format(ipadd)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                        "Reason": "Timed out", "IP_Address": ipadd}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit(0)
        except Exception as error:
            print(error)
            pass  
    except paramiko.AuthenticationException:
        exception = "AuthenticationException"
        print("Authentication failed enter valid user name and password")
        info = (
            "SSH Authentication failed when connecting to Stellar AP {0}, we cannot collect logs").format(ipadd)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                        "Reason": "AuthenticationException", "IP_Address": ipadd}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit(0)
        except Exception as error:
            print(error)
            pass 
    except paramiko.SSHException as error:
        print(error)
        exception = error.readlines()
        exception = str(exception)
        print("Device unreachable")
        logging.info(' SSH session does not establish on Stellar AP ' + ipadd)
        info = ("Stellar AP {0} is unreachable, we cannot collect logs").format(ipadd)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                        "Reason": "DeviceUnreachable", "IP_Address": ipadd}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit(0)
        except Exception as error:
            print(error)
            pass
    except:
        logging.info(' SSH session does not establish on Stellar AP, please verify SSH is enabled on the AP Group ' + ipadd)
        info = ("Stellar AP {0} is unreachable, please verify SSH is enabled on the AP Group").format(ipadd)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                        "Reason": "SSH_disabled_on_AP_Group", "IP_Address": ipadd}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit(0)
        except Exception as error:
            print(error)
            pass
    try:
        stdin, stdout, stderr = p.exec_command(cmd, timeout=120)
        #stdin, stdout, stderr = threading.Thread(target=p.exec_command,args=(cmd,))
        # stdout.start()
        # stdout.join(1200)
    except Exception:
        exception = "SSH Timeout"
        info = (
            "The python script execution on Stellar AP {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                        "Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
        sys.exit() 
    exception = stderr.readlines()
    exception = str(exception)
    connection_status = stdout.channel.recv_exit_status()
    print(connection_status)
    print(exception)
    if connection_status == 1:
        pass
    elif connection_status != 0 :
        info = (
            "The python script execution on Stellar AP {0} failed - {1}").format(ipadd, exception)
        send_message(info, jid)
        os.system('logger -t montag -p user.info ' + info)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                        "Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit(2)
        except Exception as error:
            print(error)
            pass 
    else:
        info = ("SSH Session established successfully on Stellar AP {0}").format(
            ipadd)
        os.system('logger -t montag -p user.info ' + info)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_success", "tags": {
                        "IP_Address": ipadd}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        output = stdout.readlines()
        # We close SSH Session once retrieved command output
        p.close()
        return output


def sta_limit_reached_tools(login_AP, pass_AP, ipadd):
    """ 
    This function returns file path containing the tech_support command outputs and the notification subject, body used when calling VNA API

    :param str login_AP:                   Stellar AP support login
    :param str pass_AP:                    Stellar AP support password
    :param str ipadd:                      Switch IP address
    :return:                               filename_path,subject,action,result,category
    """
    text = "More logs about the Stellar AP : {0} \n\n\n".format(ipadd)

    l_stellar_cmd = []
    l_stellar_cmd.append("ssudo tech_support_command 1")
    l_stellar_cmd.append("ssudo tech_support_command 2")
    l_stellar_cmd.append("ssudo tech_support_command 16")
    l_stellar_cmd.append("ssudo tech_support_command 27")
    l_stellar_cmd.append("ssudo tech_support_command 12 " + ip_server)
    for stellar_cmd in l_stellar_cmd:
        cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(pass_AP, login_AP, ipadd, stellar_cmd)
        try:
            output = ssh_connectivity_check(login_AP, pass_AP, ipadd, stellar_cmd)
            output = subprocess.check_output(cmd, stderr=PIPE, timeout=40, shell=True)
            if output != None:
                output = output.decode('UTF-8').strip()
                text = "{0}{1}: \n{2}\n\n".format(text, stellar_cmd, output)
            else:
                exception = "Timeout"
                info = (
                    "Timeout when establishing SSH Session to Stellar AP {0}, we cannot collect logs").format(ipadd)
                print(info)
                os.system('logger -t montag -p user.info ' + info)
                send_message(info, jid)
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                                "Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                except UnboundLocalError as error:
                    print(error)
                except Exception as error:
                    print(error)
                    pass 
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = (
                "The python script execution on Stellar AP {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                            "Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_sta_limit_reached_logs".format(
        date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = ('/opt/ALE_Script/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - The number of associated WLAN Clients to BSSID on Stellar AP {0} reached the limit").format(ipadd)
    action = "Attached to this notification the command outputs, please check if the number of associated clients corresponds to the maximum number of clients allowed per band (default: 64) "
    result = ("Stellar AP snapshot logs are collected and stored on /tftpboot/ directory on server {0}. If you observe disprecancies between the number of clients associated versus number of clients allowed please contact ALE Customer Support").format(ip_server)
    category = "sta_limit"
    return filename_path, subject, action, result, category

def vlan_limit_reached_tools(login_AP, pass_AP, ipadd):
    """ 
    This function returns file path containing the tech_support command outputs and the notification subject, body used when calling VNA API

    :param str login_AP:                   Stellar AP support login
    :param str pass_AP:                    Stellar AP support password
    :param str ipadd:                      Switch IP address
    :return:                               filename_path,subject,action,result,category
    """
    text = "More logs about the Stellar AP : {0} \n\n\n".format(ipadd)

    l_stellar_cmd = []
    l_stellar_cmd.append("ssudo tech_support_command 1")
    l_stellar_cmd.append("ssudo tech_support_command 2")
    l_stellar_cmd.append("ssudo tech_support_command 16")
    l_stellar_cmd.append("ssudo tech_support_command 21")
    l_stellar_cmd.append("ssudo tech_support_command 27")
    l_stellar_cmd.append("cat /var/config/access_role.conf")
    l_stellar_cmd.append("ssudo tech_support_command 12 " + ip_server)
    for stellar_cmd in l_stellar_cmd:
        cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(pass_AP, login_AP, ipadd, stellar_cmd)
        try:
            output = ssh_connectivity_check(login_AP, pass_AP, ipadd, stellar_cmd)
            output = subprocess.check_output(cmd, stderr=PIPE, timeout=40, shell=True)
            if output != None:
                output = output.decode('UTF-8').strip()
                text = "{0}{1}: \n{2}\n\n".format(text, stellar_cmd, output)
            else:
                exception = "Timeout"
                info = (
                    "Timeout when establishing SSH Session to Stellar AP {0}, we cannot collect logs").format(ipadd)
                print(info)
                os.system('logger -t montag -p user.info ' + info)
                send_message(info, jid)
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                                "Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                except UnboundLocalError as error:
                    print(error)
                except Exception as error:
                    print(error)
                    pass 
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = (
                "The python script execution on Stellar AP {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {
                            "Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_vlan_limit_reached_logs".format(
        date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = ('/opt/ALE_Script/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - The number of created VLAN reached the limit on Stellar AP {0}").format(ipadd)
    action = "Depending of the Stellar AP model, the VLAN count differs. AP1101/AP1201H(L) (4 VLANs), AP1201 (16 VLANs), others models (32 VLANs)"
    result = ("Stellar AP snapshot logs are collected and stored on /tftpboot/ directory on server {0}. If you observe disprecancies between the number of VLAN created versus number of VLAN allowed on your Stellar AP model, please contact ALE Customer Support").format(ip_server)
    category = "vlan_limit"
    return filename_path, subject, action, result, category

def send_file(filename_path, subject, action, result, category):
    """ 
    This function takes as argument the file containins command outputs, the notification subject, notification action and result. 
    This function is called for attaching file on Rainbow or Email notification
    :param str filename_path:                  Path of file attached to the notification
    :param str subject:                        Notification subject
    :param str action:                         Preventive Action done
    :param str result:                         Preventive Result
    :param int Card:                           Set to 0 for sending notification without card
    :param int Email:                          0 if email is disabled, 1 if email is enabled
    :return:                                   None
    """
    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_File_EMEA"
    request_debug = "Call VNA REST API Method POST path %s" % url
    print(request_debug)
    os.system('logger -t montag -p user.info Call VNA REST API Method POST')
    headers = {'Content-type': "text/plain", 'Content-Disposition': ("attachment;filename={0}_troubleshooting.log").format(category), 'jid1': '{0}'.format(
        jid), 'tata': '{0}'.format(subject), 'toto': '{0}'.format(action), 'tutu': '{0}'.format(result), 'Card': '0', 'Email': '0'}
    files = {'file': open(filename_path, 'r')}
    response = requests.post(url, files=files, headers=headers)
    print(response)
    response = str(response)
    #response = "<Response [408]>"
    response = re.findall(r"<Response \[(.*?)\]>", response)
    if "200" in response:
        os.system('logger -t montag -p user.info 200 OK')
    else:
        os.system('logger -t montag -p user.info REST API Call Failure')

if __name__ == "__main__":
    jid = "570e12872d768e9b52a8b975@openrainbow.com"
    pass_AP = "Letacla01*"
    login_AP = "support"
    ipadd = "10.130.7.70"
    cmd = "/usr/sbin/showsysinfo"
    host = "10.130.7.76"
    pass_root = ssh_connectivity_check(login_AP, pass_AP, ipadd, cmd)
#    get_snapshot_tftp(pass_root, ipadd)
    filename_path, subject, action, result, category = sta_limit_reached_tools(login_AP, pass_AP, ipadd)
    send_file(filename_path, subject, action, result, category)
    filename_path, subject, action, result, category = vlan_limit_reached_tools(login_AP, pass_AP, ipadd)
    send_file(filename_path, subject, action, result, category)