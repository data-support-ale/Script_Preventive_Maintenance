#!/usr/local/bin/python3.7

from asyncio.subprocess import PIPE
from copy import error
#from operator import sub
import sys
import os
import logging
import datetime
import time
from time import sleep
#from turtle import done
#from unicodedata import name

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

# This script contains all functions interacting with OmniSwitches

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

def execute_command(tn, command, prompt):
    tn.write(command.encode())
    result = tn.read_until(prompt.encode(), timeout=10)
    return result.decode("utf-8")

# Function SSH for checking connectivity before collecting logs
def ssh_connectivity_check(switch_user, switch_password, ipadd, cmd):
    """ 
    This function takes entry the command to push remotely on OmniSwitch by SSH with Python Paramiko module
    Paramiko exceptions are handled for notifying Network Administrator if the SSH Session does not establish

    :param str ipadd                     Command pushed by SSH on OmnISwitch
    :param str cmd                       Switch IP address
    :return:  stdout, stderr, output     If exceptions is returned on stderr a notification is sent to Network Administrator, else we log the session was established and retour CLI command outputs
    """
    print("Function ssh_connectivity_check - we execute command " + cmd)
    try:
        p = paramiko.SSHClient()
        p.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        p.connect(ipadd, port=22, username=switch_user,password=switch_password, timeout=10.0, banner_timeout=100)
    except TimeoutError as exception:
        exception = "SSH Timeout"
        print("Function ssh_connectivity_check - Exception: " + exception)
        print("Function ssh_connectivity_check - Timeout when establishing SSH Session")
        info = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "Timed out", "IP_Address": ipadd}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit(0)
        except Exception as error:
            print(error)
            pass 
    except paramiko.AuthenticationException:
        exception = "AuthenticationException"
        print("Function ssh_connectivity_check - Authentication failed enter valid user name and password")
        info = ("SSH Authentication failed when connecting to OmniSwitch {0}, we cannot collect logs or proceed for remediation action").format(ipadd)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "AuthenticationException", "IP_Address": ipadd}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit(0)
        except Exception as error:
            print(error)
            pass 
    except paramiko.SSHException as error:
        print("Function ssh_connectivity_check - " + error)
        exception = error.readlines()
        exception = str(exception)
        print("Function ssh_connectivity_check - Device unreachable")
        logging.info(' SSH session does not establish on OmniSwitch ' + ipadd)
        info = ("OmniSwitch {0} is unreachable, we cannot collect logs").format(ipadd)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "DeviceUnreachable", "IP_Address": ipadd}, "fields": {"count": 1}}])
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
        print(stdout)
        print(stderr)
    except Exception:
        exception = "SSH Exception"
        print("Function ssh_connectivity_check - " + exception)
        info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
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
    if connection_status != 0:
        info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
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
        info = ("SSH Session established successfully on OmniSwitch {0}").format(ipadd)
        os.system('logger -t montag -p user.info ' + info)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_success", "tags": {"IP_Address": ipadd}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        output = stdout.readlines()
        # We close SSH Session once retrieved command output
        p.close()
        return output


def get_file_sftp(switch_user, switch_password, ipadd, remoteFilePath, localFilePath):
    """ 
    This function takes entry the local and remote files path for downloading with sftp Paramiko client
    Paramiko exceptions are handled for notifying Network Administrator if the SSH Session does not establish
    :param str remoteFilePath            File usually located in the /flash/ directory or in /flash/python when python script executed remotely
    :param str localFilePath             Local file path usually the /tftpboot/ directory
    :param str ipadd                     Command pushed by SSH on OmnISwitch
    :param str cmd                       Switch IP address
    :return:  exception                  
    """
    date = datetime.date.today()
    ssh = paramiko.SSHClient()
    print(remoteFilePath)
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ipadd, username=switch_user,password=switch_password, timeout=10.0)
        sftp = ssh.open_sftp()
        # In case of SFTP Get timeout thread is closed and going into Exception
        try:
            th = threading.Thread(target=sftp.get, args=(remoteFilePath, localFilePath))
            th.start()
            th.join(60)
        except threading.ThreadError as error:
            print(error)
    except paramiko.AuthenticationException:
        exception = "AuthenticationException"
        print("Authentication failed enter valid user name and password")
        info = (
            "SSH Authentication failed when connecting to OmniSwitch {0}, we cannot collect logs").format(ipadd)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "AuthenticationException", "IP_Address": ipadd}, "fields": {"count": 1}}])
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
        info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "GET_SFTP_FILE", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
               print(error)
        except Exception as error:
               print(error)
        ssh.close()
        sys.exit()      
    ssh.close()


def get_pmd_file_sftp(switch_user, switch_password, ipadd, filename):
    """ 
    This function is called when a Core Dump is generated on OmniSwitch
    We extract from syslog message the pmd file path and we download with python sftp client
    :param str remoteFilePath            File  located in the /flash/pmd/ directory
    :param str localFilePath             Local file path downloaded in /tftpboot/ directory
    :param str ipadd                     Command pushed by SSH on OmnISwitch
    :param str cmd                       Switch IP address
    :return:  remote_path                  
    """
    print(filename)
    print(ipadd)
    date = datetime.date.today()
    pmd_file = filename.replace("/", "_")
    remote_path = '/tftpboot/{0}_{1}_{2}'.format(date, ipadd, filename)
    try:
        with pysftp.Connection(host=ipadd, username=switch_user, password=switch_password) as sftp:
            # get a remote file
            sftp.get('{0}'.format(filename),'/tftpboot/{0}_{1}_{2}'.format(date, ipadd, pmd_file))
    except FileNotFoundError as exception:
        print(exception)
        info = ("The download of PMD file {0} on OmniSwitch {1} failed - {2}").format(filename, ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "GET_SFTP_FILE", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        sftp.close()
        sys.exit()
    sftp.close()
    return remote_path


def format_mac(mac):
    """ 
    This function for removing delimiters and convert MAC Address into lower case
    We extract from syslog message the pmd file path and we download with python sftp client
    :param str mac            Attacker's MAC Address
    :return:  mac                  
    """
    # remove delimiters and convert to lower case
    mac = re.sub('[.:-]', '', mac).lower()
    mac = ''.join(mac.split())  # remove whitespaces
    assert len(mac) == 12  # length should be now exactly 12 (eg. 008041aefd7e)
    assert mac.isalnum()  # should only contain letters and numbers
    # convert mac in canonical form (eg. 00:80:41:ae:fd:7e)
    mac = ":".join(["%s" % (mac[i:i+2]) for i in range(0, 12, 2)])
    return mac


def file_setup_qos(addr):
    """ 
    This function takes as argument the IP or MAC Address of the Attacker and fil-in the configqos file for applying the Policy Rule to prevent access to the network
    We extract from syslog message the pmd file path and we download with python sftp client
    :param str addr            IP or MAC Address of the Attacker
    """
    content_variable = open('/opt/ALE_Script/configqos', 'w')
    if re.search(r"\:", addr):  # mac
        setup_config = "policy condition scanner_{0} source mac {0}\npolicy action block_mac disposition deny\npolicy rule scanner_{0} condition scanner_{0} action block_mac\nqos apply\nqos enable\n".format(
            addr)
    else:
        setup_config = "policy condition scanner_{0} source ip {0}\npolicy action block_ip disposition deny\npolicy rule scanner_{0} condition scanner_{0} action block_ip\nqos apply".format(
            addr)
    content_variable.write(setup_config)
    content_variable.close()

# Function debug enable or disable
def debugging(switch_user, switch_password, ipadd, appid, subapp, level):
    """ 
    This function takes entries arguments the appid, subapp and level to apply on switch for enabling (level debug1, debug2) or disabling debug logs (level info)

    :param str appid_1:               swlog appid function (ipv4,bcmd)
    :param str subapp_1:              swlog subapp component (all)
    :param str level_1:               swlog debug level (debug1,debug2,debug3,info)
    :script executed ssh_device:      with cmd in argument
    :return:                          None
    """

    cmd = ("swlog appid {0} subapp {1} level {2}").format(appid, subapp, level)
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)


def enable_port(user, password, ipadd, portnumber):
    """ 
    This function enables the port where there is a loop detected on the OmniSwitch put in arguments.
    :param str user:                Switch user login
    :param str password:            Switch user password
    :param str ipadd:               Switch IP Address
    :param str portnumber:          The Switch port where there is a loop. shape : x/y/z with x = chassis n ; y = slot n ; z = port n
    :return:                        None
    """
    cmd = "interfaces port {0} admin-state enable".format(portnumber)
    # ssh session to start python script remotely
    os.system('logger -t montag -p port enabling')
    os.system(
        "sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(password, user, ipadd, cmd))
    os.system(
        'logger -t montag -p user.info Following port is administratively enabled: ' + portnumber)

# Function to collect tech_support_complete.tar file by SFTP
def get_tech_support_sftp(switch_user, switch_password, host, ipadd):
    """ 
    This function takes entries arguments the OmniSwitch IP Address
    This function returns file path containing the tech_support_complete file and the notification subject, body used when calling VNA API

    :param str host:                        Switch Hostname
    :param str ipadd:                       Switch IP address
    :return:                                filename_path,subject,action,result,category
    """
    date = datetime.date.today()
    date_hm = datetime.datetime.today()
    filename = 'tech_support_complete.tar'
    try:
        p = paramiko.SSHClient()
        p.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        p.connect(ipadd, port=22, username=switch_user, password=switch_password)
    except paramiko.AuthenticationException:
        exception = "AuthenticationException"
        print("Authentication failed enter valid user name and password")
        info = ("SSH Authentication failed when connecting to OmniSwitch {0}, we cannot collect logs").format(ipadd)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "AuthenticationException", "IP_Address": ipadd}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit(0)
        except Exception as error:
            print(error)
            pass 
    except paramiko.SSHException as error:
        exception = error.readlines()
        exception = str(exception)
        print("Timeout when establishing SSH Session on OmniSwitch " + ipadd)
        info = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "Timeout", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        sys.exit()
    cmd = ("rm -rf {0}").format(filename)
    stdin, stdout, stderr = p.exec_command(cmd)
    exception = stderr.readlines()
    exception = str(exception)
    connection_status = stdout.channel.recv_exit_status()
    if connection_status != 0:
        info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        send_message(info, jid)
        os.system('logger -t montag -p user.info ' + info)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        sys.exit(2)

    stdin, stdout, stderr = p.exec_command("show tech-support eng complete")
    exception = stderr.readlines()
    exception = str(exception)
    connection_status = stdout.channel.recv_exit_status()
    if connection_status != 0:
        info = ("\"The show tech support eng complete\" command on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        send_message(info, jid)
        os.system('logger -t montag -p user.info ' + info)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        sys.exit(2)

    cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2}  ls | grep {3}".format(
        switch_password, switch_user, ipadd, filename)
    run = cmd.split()
    out = ''
    i = 0
    while not out:
        print(" Tech Support file creation under progress.", end="\r")
        sleep(2)
        print(" Tech Support file creation under progress..", end="\r")
        sleep(2)
        print(" Tech Support file creation under progress...", end="\r")
        print(i)
        sleep(2)
        p = subprocess.Popen(run, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        out = out.decode('UTF-8').strip()
        if i > 20:
            print("Tech Support file creation timeout")
            sys.exit(2)

    filename = "tech_support_complete.tar"
    remoteFilePath = "./tech_support_complete.tar"
    localFilePath = "/tftpboot/{0}_{1}-{2}_{3}_{4}".format(date,date_hm.hour,date_hm.minute,ipadd,filename)
    #### SFTP GET tech support #####
    get_file_sftp(switch_user, switch_password, ipadd, remoteFilePath, localFilePath)
    print(localFilePath) #/tftpboot/2022-03-24_18-41_10.130.7.246_tech_support_complete.tar
    subject = ("Preventive Maintenance Application - Show Tech-Support Complete command executed on switch: {0}").format(ipadd)
    action = ("The Show Tech-Support Complete file {0} is collected from OmniSwitch (Hostname: {1})").format(localFilePath, host)
    result = "Find enclosed to this notification the tech_support_complete.tar file"
    category = "tech_support_complete"
    return localFilePath, subject, action, result, category

# Function to collect several command outputs related to TCAM failure
def collect_command_output_tcam(switch_user, switch_password, host, ipadd):
    """ 
    This function takes entries arguments the OmniSwitch IP Address where TCAM (QOS) failure is noticed.
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show qos config; show qos statistics; show qos log; show qos rules; show tcam utilization detail")

    for switch_cmd in l_switch_cmd:
        try:
            output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output_decode)
            else:
                exception = "Timeout"
                info = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                os.system('logger -t montag -p user.info ' + info)
                send_message(info, jid)
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                except UnboundLocalError as error:
                    print(error)
                except Exception as error:
                    print(error)
                    pass 
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = ( "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_tcam_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = ('/opt/ALE_Script/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - A TCAM failure (QOS) is noticed on switch: {0}, reason {1}").format(ipadd, source)
    action = ("A TCAM failure (QOS) is noticed on OmniSwitch (Hostname: {0})").format(host)
    result = "Find enclosed to this notification the log collection of command outputs"
    category = "qos"
    return filename_path, subject, action, result, category

# Function to collect several command outputs related to Network Loop
def collect_command_output_network_loop(switch_user, switch_password, ipadd, port):
    """ 
    This function takes entries arguments the OmniSwitch IP Address where Network Loop is noticed.
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str port:                  Switch Interface port where loop is noticed
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show system; show chassis")      
    l_switch_cmd.append("show interfaces " + port + " status")
    l_switch_cmd.append("show mac-learning port " + port)
    l_switch_cmd.append("show vlan members port " + port)

    for switch_cmd in l_switch_cmd:
        os.system('logger -t montag -p user.info SSH session for show chassis')
        try:
            output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output_decode)
            else:
                exception = "Timeout"
                info = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                os.system('logger -t montag -p user.info ' + info)
                send_message(info, jid)
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                except UnboundLocalError as error:
                    print(error)
                except Exception as error:
                    print(error)
                    pass 
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_network_loop_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = ('/opt/ALE_Script/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - A loop has been detected on your network and the port {0} is administratively disabled on device {1}").format(port,ipadd)
    action = ("A Network Loop is noticed on OmniSwitch: {0} and we have deactivated the interface administratively").format(ipadd)
    result = ("Find enclosed to this notification the log collection of last 5 minutes and interface port {0} status").format(port)
    category = "network_loop"
    return filename_path, subject, action, result, category

# Function to collect several command outputs related to Cloud-Agent (OV Cirrus) failure
def collect_command_output_ovc(switch_user, switch_password, vpn_ip, reason, host, ipadd):
    """ 
    This function takes entries arguments the OmniSwitch IP Address where cloud-agent is enabled
    This function checks the VPN IP address and failure reason received from Admin: 
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str vpn_ip:                OVC VPN Far End IP Address
    :param str reason:                OPENVPN or OVCMM failure reason
    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show system; show cloud-agent status; show cloud-agent vpn status; show ntp server status; show log swlog | grep 'openvpn\|ovcCmm'; cat libcurl_log")

    if vpn_ip != "0":
        l_switch_cmd.append("ping " + vpn_ip)
        l_switch_cmd.append("traceroute " + vpn_ip + " max-hop 3")

    for switch_cmd in l_switch_cmd:
        try:
            output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output_decode)
            else:
                exception = "Timeout"
                info = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                os.system('logger -t montag -p user.info ' + info)
                send_message(info, jid)
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                except UnboundLocalError as error:
                    print(error)
                except Exception as error:
                    print(error)
                    pass 
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_ovc_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = ('/opt/ALE_Script/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    if reason == "Cannot resolve host address":
        subject = ("Preventive Maintenance Application - OVC Activation Server is unreachable from OmniSwitch {0} therefore VPN is DOWN").format(host)
        action = ("Please verify OmniSwitch {0} can do name resolution - add commands ip name server x.x.x.x and ip domain-lookup").format(host)
        result = "Find enclosed to this notification the log collection"          
    elif reason == "S_errno_EHOSTUNREACH" or reason == "S_errno_ETIMEDOUT":
        subject = ("Preventive Maintenance Application - OVC Activation Server is unreachable from OmniSwitch {0} therefore VPN is DOWN").format(host)
        action = ("Please verify OVC Activation Server activation.myovcloud.com is reachable - this FQDN must be resolved by DNS set on OmniSwitch {0} and accessible from outside").format(host)
        result = "Find enclosed to this notification the log collection"   
    elif reason == "Invalid process status":
        subject = ("Preventive Maintenance Application - Cloud-Agent module is into Invalid Status on OmniSwitch {0}").format(host)
        action = ("No action done on OmniSwitch (Hostname: {0}), please ensure the Serial Number is added in the OV Cirrus Device Catalog").format(host)
        result = "Find enclosed to this notification the log collection"
    category = "ovc"
    return filename_path, subject, action, result, category


# Function to collect several command outputs related to MQTT failure
def collect_command_output_mqtt(switch_user, switch_password, ovip, host, ipadd):
    """ 
    This function takes entries arguments the OmniVista IP Address used for Device Profiling  
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str ovip:                  OmniVista IP Address (e.g. 143.209.0.2:1883)
    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show device-profile config; show appmgr iot-profiler")

    for switch_cmd in l_switch_cmd:
        try:
            output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output_decode)
            else:
                exception = "Timeout"
                info = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                os.system('logger -t montag -p user.info ' + info)
                send_message(info, jid)
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                except UnboundLocalError as error:
                    print(error)
                except Exception as error:
                    print(error)
                    pass 
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_mqtt_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = ('/opt/ALE_Script/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - Device Profiling (aka IoT Profiling)  module is enabled on OmniSwitch {0} but unable to connect to OmniVista IP Address: {1}").format(host, ovip)
    action = ("No action done on OmniSwitch (Hostname: {0}), please check the IP connectivity with OmniVista, note that Device Profiling is not a VRF-aware feature").format(host)
    result = "Find enclosed to this notification the log collection"
    category = "mqtt"
    return filename_path, subject, action, result, category


# Function to collect several command outputs related to Unexpected traffic (storm) detected
def collect_command_output_storm(switch_user, switch_password, port, source, decision, host, ipadd):
    """ 
    This function takes entries arguments the Interface/Port where storm occurs and the type of traffic. 
    This function checks the decision received from Admin:
       if decision is 1, Administrator selected Yes and script disables the interface
       if decision is 0, Administrator selected No and we only provide command outputs  
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str port:                  Switch Interface/Port ID <chasis>/<slot>/>port>
    :param str source:                Switch Traffic type (broadcast, multicast, unknown unicast)
    :param int desicion:              Administrator decision (1: 'Yes', 0: 'No')
    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
    ## Log collection of additionnal command outputs
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show health port " + port)
    l_switch_cmd.append("show interfaces " + port)
    sleep(2)
    l_switch_cmd.append("show interfaces " + port)
    sleep(2)
    l_switch_cmd.append("show interfaces " + port)
    l_switch_cmd.append("show interfaces " + port + " flood-rate")
    if decision == "1" or decision == "2":
        l_switch_cmd.append("interfaces port " + port + " admin-state disable")
    for switch_cmd in l_switch_cmd:
        try:
            output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output_decode)
            else:
                exception = "Timeout"
                info = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                os.system('logger -t montag -p user.info ' + info)
                send_message(info, jid)
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                except UnboundLocalError as error:
                    print(error)
                except Exception as error:
                    print(error)
                    pass 
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_storm_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = ('/opt/ALE_Script/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - Unexpected traffic (storm) detected on switch: {0}, reason {1}").format(ipadd, source)
    if decision == "1" or decision == "2":
        action = ("The Interface {0} is administratively disabled on OmniSwitch (Hostname: {1})").format(port, host)
        result = "Find enclosed to this notification the log collection of actions done"
    else:
        action = ("No action done on OmniSwitch (Hostname: {0})").format(host)
        result = "Find enclosed to this notification the interface's status/statistics"
    category = "storm"
    return filename_path, subject, action, result, category


# Function to collect several command outputs related to Port Violation
def collect_command_output_violation(switch_user, switch_password, port, source, decision, host, ipadd):
    """ 
    This function takes entries arguments the Interface/Port where violation occurs. 
    This function checks the decision received from Admin:
       if decision is 1, Administrator selected Yes and script clears the violation
       if decision is 0, Administrator selected No and we only provide command outputs
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str port:                  Switch Interface/Port ID <chasis>/<slot>/>port>
    :param str source:                Switch Violation reason (lbd, Access Guardian, lps)
    :param int desicion:              Administrator decision (1: 'Yes', 0: 'No')
    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show interfaces " + port + " status")
    if decision == "1":
        l_switch_cmd.append("clear violation port " + port)
    l_switch_cmd.append("show violation; show violation port " + port)

    for switch_cmd in l_switch_cmd:
        try:
            output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output_decode)
            else:
                exception = "Timeout"
                info = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                os.system('logger -t montag -p user.info ' + info)
                send_message(info, jid)
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                except UnboundLocalError as error:
                    print(error)
                except Exception as error:
                    print(error)
                    pass 
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_violation_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = ('/opt/ALE_Script/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - Port violation noticed on switch: {0}, reason {1}").format(ipadd, source)
    if decision == "1":
        action = ("The Port {0} is cleared from violation table on OmniSwitch (Hostname: {1})").format(port, host)
        result = "Find enclosed to this notification the log collection of actions done"
    else:
        action = ("No action done on OmniSwitch (Hostname: {0})").format(host)
        result = "Find enclosed to this notification the log collection"
    result = "Find enclosed to this notification the log collection of actions done"
    category = "violation"
    return filename_path, subject, action, result, category

# Function to collect several command outputs related to SPB issue
def collect_command_output_spb(switch_user, switch_password, host, ipadd):
    """ 
    This function takes entries arguments the OmniSwitch IP Address
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show spb isis adjacency; show spb isis interface")

    for switch_cmd in l_switch_cmd:
        try:
            output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output_decode)
            else:
                exception = "Timeout"
                info = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                os.system('logger -t montag -p user.info ' + info)
                send_message(info, jid)
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                except UnboundLocalError as error:
                    print(error)
                except Exception as error:
                    print(error)
                    pass 
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_spb_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = ('/opt/ALE_Script/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - SPB Adjacency issue detected on switch: {0}").format(ipadd)
    action = ("A SPB adjacency is down on OmniSwitch (Hostname: {0})").format(host)
    result = "Find enclosed to this notification the log collection for further analysis"
    category = "spb"
    return filename_path, subject, action, result, category

# Function to collect/enable Spanning for specific VLAN
def collect_command_output_stp(switch_user, switch_password, decision, host, ipadd, vlan):
    """ 
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API
    This function checks the decision received from Admin:
       if decision is 1, Administrator selected Yes and script clears the violation
       if decision is 0, Administrator selected No and we only provide command outputs
    :param str vlan:                  Switch VLAN Number where Spanning tree is detected as disabled
    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show microcode; show system; show spantree mode")
    l_switch_cmd.append("show spantree vlan " + vlan)
    l_switch_cmd.append("show " + vlan)
    if decision == "1":
        l_switch_cmd.append("spantree vlan" + vlan + "admin-state enable")    

    for switch_cmd in l_switch_cmd:
        try:
            output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output_decode)
            else:
                exception = "Timeout"
                info = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                os.system('logger -t montag -p user.info ' + info)
                send_message(info, jid)
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                except UnboundLocalError as error:
                    print(error)
                except Exception as error:
                    print(error)
                    pass 
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_stp_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = ('/opt/ALE_Script/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()

    subject = ("Preventive Maintenance Application - STP configuration issue detected on switch: {0}").format(ipadd)
    if decision == "1":
        action = ("Decision set to Yes. The Spanning Tree on VLAN {0} is enabled on OmniSwitch (Hostname: {1})").format(vlan,host)
        result = "Find enclosed to this notification the log collection for further analysis"
    else:
        action = ("The Spanning Tree on VLAN {0} is not enabled on OmniSwitch (Hostname: {1})").format(vlan,host)
        result = "Find enclosed to this notification the log collection for further analysis"       
    category = "stp"
    return filename_path, subject, action, result, category


# Function to collect several command outputs related to FAN failure
def collect_command_output_fan(switch_user, switch_password, host, ipadd):
    """ 
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category, chassis_id
    """
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append('show microcode; show system; show fan; show temperature')

    for switch_cmd in l_switch_cmd:
        try:
            output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output_decode)
            else:
                exception = "Timeout"
                info = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                os.system('logger -t montag -p user.info ' + info)
                send_message(info, jid)
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                except UnboundLocalError as error:
                    print(error)
                except Exception as error:
                    print(error)
                    pass 
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
        except subprocess.SubprocessError as exception:
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_fan_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = ('/opt/ALE_Script/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    
    ### We are looking for fan chassis_ID
    switch_cmd = "show fan"
    fan_status=0
    try:
        output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
        print(output)
        if output != None:
            output = str(output)
            fan_status = bytes(output, "utf-8").decode("unicode_escape")
            fan_status = fan_status.replace("', '","")
            fan_status = fan_status.replace("']","")
            fan_status = fan_status.replace("['","")
            print(fan_status)
    except subprocess.TimeoutExpired as exception:
        info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        sys.exit()
    except subprocess.SubprocessError as exception:
        info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        sys.exit()
    if "NO" in fan_status:
        try:
            chassis_id = re.findall(r"(.*?)/--         1       NO", fan_status)[0]
            print(chassis_id)
        except IndexError:
            print("Index error in regex")
            exit()
    else:
        print("FAN Chassis ID Not found we set value Unknown")
        chassis_id="Unknown"

    subject = ("Preventive Maintenance Application - FAN issue detected on switch: {0}").format(ipadd)
    action = ("The FAN Unit {0} is inoperable on OmniSwitch (Hostname: {1})").format(chassis_id,host)
    result = "Find enclosed to this notification the log collection for further analysis"
    category = "fan"
    return filename_path, subject, action, result, category, chassis_id


# Function to collect several command outputs related to Power Supply
def collect_command_output_ps(switch_user, switch_password, psid, host, ipadd):
    """ 
    This function takes entries arguments the Power Supply ID. This function is called when an issue is observed on Power Supply hardware
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str psid:                  Switch Power Supply ID
    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show powersupply; show powersupply total")
    l_switch_cmd.append('echo \"i2cset -y -f 1 0x77 0x1;i2cset -y -f 1 0x60 0x92 0x80\" | su')
    sleep(1)
    l_switch_cmd.append('echo \"i2cset -y -f 1 0x77 0x1;i2cset -y -f 1 0x60 0x92 0x00\" | su')
    sleep(2)
    l_switch_cmd.append('echo \"i2cset -y -f 1 0x77 0x1;i2cget -y -f 1 0x60 0x90\" | su')
    sleep(1)
    l_switch_cmd.append('echo \"i2cset -y -f 1 0x77 0x1;i2cget -y -f 1 0x60 0x92\" | su')

    for switch_cmd in l_switch_cmd:
        try:
            output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
            print(output)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output_decode)
            else:
                exception = "Timeout"
                info = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                os.system('logger -t montag -p user.info ' + info)
                send_message(info, jid)
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                except UnboundLocalError as error:
                    print(error)
                except Exception as error:
                    print(error)
                    pass 
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()

    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_ps_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = ('/opt/ALE_Script/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - Power Supply issue detected on switch: {0}").format(ipadd)
    if psid == "Unknown":
        action = ("A Power Supply unit  is down or running abnormal \"Power Supply operational state changed to UNPOWERED\" on OmniSwitch (Hostname: {1})").format(psid, host)
    else:
        action = ("The Power Supply unit {0} is down or running abnormal on OmniSwitch (Hostname: {1})").format(psid, host)
    result = "Find enclosed to this notification the log collection for further analysis"
    category = "ps"
    return filename_path, subject, action, result, category

# Function to collect several command outputs related to Virtual Chassis
def collect_command_output_vc(switch_user, switch_password, vcid, host, ipadd):
    """ 
    This function takes entries arguments the Virtual Chassis ID and the Switch System Name. This function is called when an issue is observed on Virtual Chassis category
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str vcid:                  Switch Virtual Chassis ID
    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show virtual-chassis vf-link; show virtual-chassis auto-vf-link-port; show virtual-chassis neighbors; debug show virtual-chassis topology")

    for switch_cmd in l_switch_cmd:
        try:
            output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output_decode)
            else:
                exception = "Timeout"
                info = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                os.system('logger -t montag -p user.info ' + info)
                send_message(info, jid)
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                except UnboundLocalError as error:
                    print(error)
                except Exception as error:
                    print(error)
                    pass 
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
        except subprocess.SubprocessError as exception:
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_vcmm_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = ('/opt/ALE_Script/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - Virtual Chassis issue detected on switch: {0}").format(ipadd)
    action = ("The VC CMM {0} is down on VC (Hostname: {1}) syslogs").format(vcid, host)
    result = "Find enclosed to this notification the log collection for further analysis"
    category = "vcmm"
    return filename_path, subject, action, result, category

# Function to collect several command outputs related to Linkagg
def collect_command_output_linkagg(switch_user, switch_password, agg, host, ipadd):
    """ 
    This function takes entries arguments the Link Aggregation ID. This function is called when an issue is observed on Linkagg category
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str agg:                   Link Aggregation ID
    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show interfaces alias; show linkagg")
    l_switch_cmd.append("show linkagg agg " + agg)
    l_switch_cmd.append("show linkagg agg " + agg + " port")

    for switch_cmd in l_switch_cmd:
        try:
            output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output_decode)
            else:
                exception = "Timeout"
                info = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                os.system('logger -t montag -p user.info ' + info)
                send_message(info, jid)
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                except UnboundLocalError as error:
                    print(error)
                except Exception as error:
                    print(error)
                    pass 
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
        except subprocess.SubprocessError as exception:
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_linkagg_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = ('/opt/ALE_Script/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - A LinkAgg Port Leave occurs on OmniSwitch: {0}").format(ipadd)
    action = ("A Linkagg issue has been detected in switch(Hostname: {0}) Aggregate ID {1}").format(host, agg)
    result = "Find enclosed to this notification the log collection for further analysis"
    category = "linkagg"
    return filename_path, subject, action, result, category



# Function to collect several command outputs related to PoE
def collect_command_output_poe(switch_user, switch_password, host, ipadd, port, reason):
    """ 
    This function takes IP Address and Hostname, port number (without unit/slot) and faulty reason as argument. This function is called when an issue is observed on Lanpower category
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API
    :param str port:                  Switch port without unit/slot
    :param str reason:                LANPOWER faulty reason ex: Non-standard PD connected
    :param str ipadd:                 Switch IP address
    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show interfaces alias; show system; show lldp remote-system; show configuration snapshot lanpower; \
        show powersupply total; show lanpower slot 1/1 ; show lanpower slot 1/1 port-config; show lanpower power-rule; show lanpower chassis 1 capacitor-detection; \
        show lanpower chassis 1 usage-threshold; show lanpower chassis 1 ni-priority; show lanpower slot 1/1 high-resistance-detection; \
        show lanpower slot 1/1 priority-disconnect; show lanpower slot 1/1 class-detection")

    for switch_cmd in l_switch_cmd:
        try:
            output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output_decode)
            else:
                exception = "Timeout"
                info = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                os.system('logger -t montag -p user.info ' + info)
                send_message(info, jid)
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                except UnboundLocalError as error:
                    print(error)
                except Exception as error:
                    print(error)
                    pass 
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
        except subprocess.SubprocessError as exception:
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass  
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_poe_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = ('/opt/ALE_Script/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    lanpower_settings_status = 0
    switch_cmd = "show configuration snapshot lanpower"
    try:
        output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
        print(output)
        if output != None:
            output = str(output)
            output_decode = bytes(output, "utf-8").decode("unicode_escape")
            output_decode = output_decode.replace("', '","")
            output_decode = output_decode.replace("']","")
            lanpower_settings_status = output_decode.replace("['","")
            #lanpower_settings_status = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
            #lanpower_settings_status = lanpower_settings_status.decode('UTF-8').strip()
            print(lanpower_settings_status)
    except subprocess.TimeoutExpired as exception:
        info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        sys.exit()
    except subprocess.SubprocessError as exception:
        info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        sys.exit()
    if "capacitor-detection enable" in lanpower_settings_status:
        print("Capacitor detection enabled!")
        capacitor_detection_status = "enabled"
    else:
        capacitor_detection_status = "disabled"
    if "high-resistance-detection enable" in lanpower_settings_status:
        print("High Resistance detection enabled!")
        high_resistance_detection_status = "enabled"
    else:
        high_resistance_detection_status = "disabled"
    if reason == "(Illegal class)":
        subject = ("Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port 1/1/{2} - reason {3}").format(host,ipadd,port,reason)
        action = ("A PoE issue has been detected in switch(Hostname : {0}) syslogs with reason {1}. The OmniSwitch POE controller requires that the same class be detected on both pairs before passing detection and sending POE power to the port. When it detects different classes from the same device, power is denied until 4pair is disabled").format(host, reason)
        result = "Find enclosed to this notification the log collection for further analysis"
    else:
        subject = ("Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port 1/1/{2} - reason {3}").format(host,ipadd,port,reason)
        action = ("A PoE issue has been detected in switch(Hostname : {0}) syslogs. Capacitor Detection is {1}, High Resistance Detection is {2}").format(host, capacitor_detection_status, high_resistance_detection_status)
        result = "Find enclosed to this notification the log collection for further analysis"
    category = "poe"
    return filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status


# Function to collect OmniSwitch IP Service/AAA Authentication status based on protocol received as argument
def collect_command_output_aaa(switch_user, switch_password, protocol, ipadd):
    """ 
    This function takes IP Address and protocol as argument. This function is called when an authentication failure is noticed for specified protocol
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API
    :param str protocol:                  AAA Protocol (HTTPS, FTP, TELNET, SSH, NTP, SNMP, RADIUS)
    :param str ipadd:                     Switch IP address
    :return:                              filename_path,subject,action,result,category
    """
    service_status = 0
    protocol_a = 0
    if protocol == "HTTPS":
        protocol_a == "http"
    switch_cmd = "show ip service | grep {0}".format(protocol_a)
    try:
        output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
        print(output)
        if output != None:
            output = str(output)
            service_status=0
            output_decode = bytes(output, "utf-8").decode("unicode_escape")
            output_decode = output_decode.replace("', '","")
            output_decode = output_decode.replace("']","")
            service_status = output_decode.replace("['","")
    except subprocess.TimeoutExpired as exception:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        sys.exit()
    except AttributeError as exception:
        info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        sys.exit()
    except FileNotFoundError as exception:
        info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        sys.exit()
    if "enabled" in service_status:
        print("Protocol " + protocol + " enabled!")
        service_status = "enabled"
    else:
        service_status = "disabled"

    switch_cmd = "show configuration snapshot aaa | grep \"aaa authentication {0}\"".format(protocol)
    aaa_status=0
    try:
        output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
        print(output)
        if output != None:
            output = str(output)
            output_decode = bytes(output, "utf-8").decode("unicode_escape")
            output_decode = output_decode.replace("', '","")
            output_decode = output_decode.replace("']","")
            aaa_status = output_decode.replace("['","")
            print(aaa_status)
        try:
            if "aaa authentication" in aaa_status:
                aaa_status = "enabled"
            else:
                aaa_status = "disabled"
        except:
            aaa_status = "disabled"
            pass
    except subprocess.TimeoutExpired as exception:
        info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        sys.exit()
    except subprocess.CalledProcessError as e:
        aaa_status = "disabled"
    except AttributeError as exception:
        info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        sys.exit()
    except FileNotFoundError as exception:
        info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        sys.exit()
    print(aaa_status)
    return service_status, aaa_status


def authentication_failure(switch_user, switch_password, user, source_ip, protocol, service_status, aaa_status, host, ipadd):
    """ 
    This function takes entries arguments the Protocol service status, Protocol aaa authentication status as well as User login, destination protocol, source IP Address. This function is called when an authentication failure is noticed
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str user:                       User login trying to authenticate on OmniSwitch
    :param str source_ip:                  Source IP Address of the User
    :param str protocol:                   AAA Protocol (HTTPS, FTP, TELNET, SSH, NTP, SNMP, RADIUS)
    :param str service_status:             Protocol Service status (enabled,disabled)
    :param str aaa_status:                 Protocol Authentication stauts (enabled,disabled)
    :param str host:                       Switch Hostname
    :param str ipadd:                      Switch IP address
    :return:                               filename_path,subject,action,result,category
    """
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show ip service; show aaa authentication")

    for switch_cmd in l_switch_cmd:
        try:
            output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output_decode)
            else:
                exception = "Timeout"
                info = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                os.system('logger -t montag -p user.info ' + info)
                send_message(info, jid)
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                except UnboundLocalError as error:
                    print(error)
                except Exception as error:
                    print(error)
                    pass 
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
        except subprocess.SubprocessError as exception:
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_authentication_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = ('/opt/ALE_Script/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - Authentication failure noticed on switch: {0}").format(ipadd)
    action = ("An Authentication failure has been detected in switch( Hostname: {0} ) from User: {1} - source IP Address: {2} - protocol: {3}").format(host, user, source_ip, protocol)
    result = ("As per configuration, this service protocol is {0} and aaa authentication is {1}").format(service_status, aaa_status)
    category = "authentication"
    return filename_path, subject, action, result, category

# Function to collect OmniSwitch LLDP Remote System Port Description
def collect_command_output_lldp_port_description(switch_user, switch_password, port, ipadd):
    """ 
    This function takes IP Address and port as argument. This function is called when we want additionnal information on equipment connected to Switch Interface
    This function returns LLDP Port Description field value
    :param str port:                      Switch Interface Port
    :param str ipadd:                     Switch IP address
    :return:                              lldp_port_description
    """
    lldp_port_description = lldp_mac_address = 0

    switch_cmd = "show lldp port {0} remote-system".format(port)
    try:
        output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
        print(output)
        if output != None:
            output = str(output)
            output_decode = bytes(output, "utf-8").decode("unicode_escape")
            output_decode = output_decode.replace("', '","")
            output_decode = output_decode.replace("']","")
            lldp_port = output_decode.replace("['","")
    except subprocess.TimeoutExpired as exception:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        sys.exit()
    except AttributeError as exception:
        info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        sys.exit()
    except FileNotFoundError as exception:
        info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        sys.exit()
    if "Port Description" in lldp_port:
        try: 
           print(lldp_port)
           lldp_port_description = re.findall(r"Port Description            = (.*?),", lldp_port)[0]
           lldp_mac_address = re.findall(r"Port (.*?):\n", lldp_port)[1]
        except exception as error:
            print(error)
            lldp_port_description = lldp_mac_address = 0
            pass
    return lldp_port_description, lldp_mac_address

# Function to collect OmniSwitch LLDP Remote System Port Description
def get_arp_entry(switch_user, switch_password, lldp_mac_address, ipadd):
    """ 
    This function takes Switch IP Address and Device MAC Address. This function is called when we want to find the Device IP Address from ARP Table
    This function returns LLDP Port Description field value
    :param str lldp_mac_address:          Device MAC Address found from LLDP Port Description
    :param str ipadd:                     Switch IP address
    :return:                              device_ip
    """
    device_ip = 0

    switch_cmd = "show arp | grep \"{0}\"".format(lldp_mac_address)
    try:
        output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
        print(output)
        if output != None:
            output = str(output)
            output_decode = bytes(output, "utf-8").decode("unicode_escape")
            output_decode = output_decode.replace("', '","")
            output_decode = output_decode.replace("']","")
            device_ip = output_decode.replace("['","")
    except subprocess.TimeoutExpired as exception:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        sys.exit()
    except AttributeError as exception:
        info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        sys.exit()
    except FileNotFoundError as exception:
        info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        send_message(info, jid)
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass 
        sys.exit()
    if "{0}".format(lldp_mac_address) in device_ip:
        print(device_ip)
        device_ip = re.findall(r" ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}) ", device_ip)[0]
    print(device_ip)
    return device_ip

def check_save(ipadd, port, type):
    """ 
    This function takes entries OmniSwitch IP Address, port and type (corresponds to use case)

    :param str type:                       Use case (duplicate if duplicate IP, fan if fan failure ....)
    :param str port:                       Switch Hostname
    :param str ipadd:                      Switch IP address
    :return int:                           Return 1 if always, -1 if never else 0 if no entry
    """
    if not os.path.exists('/opt/ALE_Script/decisions_save.conf'):
        open('/opt/ALE_Script/decisions_save.conf', 'w', errors='ignore').close()
        return "0"

    content = open("/opt/ALE_Script/decisions_save.conf", "r", errors='ignore')
    file_lines = content.readlines()
    content.close()

    for line in file_lines:
        print(line)
        if "{0},{1},{2},always".format(ipadd, port, type) in line:
            return "1"
        if "{0},{1},{2},never".format(ipadd, port, type) in line:
            return "-1"

    return '0'



def add_new_save(ipadd, port, type, choice="never"):
    """ 
    This function saves the new instruction received when Administrator clicks on a Rainbow Adaptive card button (Yes, No, Yes and remember, other)
    :param str ipadd:              Switch IP Address
    :param str portnumber:         Switch port number
    :param str type:               Which use case: loop, flapping
    :return:                       None
    """

    if not os.path.exists('/opt/ALE_Script/decisions_save.conf'):
        try:
            open('/opt/ALE_Script/decisions_save.conf', 'w').close()
            subprocess.call(['chmod', '0755', '/opt/ALE_Script/decisions_save.conf'])
        except OSError as error:
            print(error)
            print("Permission error when creating file /opt/ALE_Script/decisions_save.conf")
            sys.exit()

    fileR = open("/opt/ALE_Script/decisions_save.conf", "r", errors='ignore')
    text = fileR.read()
    fileR.close()

    textInsert = "{0},{1},{2},{3}\n".format(ipadd, port, type, choice)
    try:
        fileW = open("/opt/ALE_Script/decisions_save.conf", "w", errors='ignore')
        fileW.write(textInsert + text)
        fileW.close()
    except OSError as error:
        print(error)
        print("Permission error when creating file /opt/ALE_Script/decisions_save.conf")
        sys.exit()

def script_has_run_recently(seconds,ip,function):
    """ 
    This function is called on scenario when we prevent to run the script again and again because we receive remanent logs or further logs after 1st notification was sent
    :param str seconds:              Runtime
    :param str ip:                   Switch IP Address
    :param str function:             Which use case: loop, flapping
    :return:                         True (if runtime less than 5 minutes) or False
    """
    filename = ('/opt/ALE_Script/last-runtime_{0}.txt').format(function)
    current_time = int(time.time())
    text = "{0},{1},{2}\n".format(str(current_time),ip, function)
    try:
        content = open("/opt/ALE_Script/last-runtime_{0}.txt".format(function), "r", errors='ignore')
 #       with open(filename, 'rt') as f:
        file_lines = content.readlines()
        file_lines = file_lines[0]
        file_lines = file_lines.split(',')
        content.close()
        last_run = int(file_lines[0])
#            last_run = int(f.read().strip())
    except (IOError, ValueError) as e:
        last_run = 0
    if last_run + seconds > current_time:
        if check_timestamp_and_function(ip, function) == 2:
           print("IP Address and function found in last-runtime + last run less than 5 minutes")
           return True
        if check_timestamp_and_function(ip, function) == 1:
            with open(filename, 'w') as f:
               f.write(text)
    else:
        with open(filename, 'wt') as f:
            f.write(text)
        return False

def check_timestamp_and_function(ip, function):
    """ 
    This function is called by function script_has_run_recently
    :param str ip:                   Switch IP Address
    :param str function:             Which use case: loop, flapping
    :return:                         2  (if runtime + function found) else 1
    """   
    content = open("/opt/ALE_Script/last-runtime_{0}.txt".format(function), "r", errors='ignore')
    file_lines = content.readlines()
    content.close()

    for line in file_lines:
        print(line)
        if "{0},{1}".format(ip, function) in line:
            print("IP Address and function found in last-runtime")
            return 2
        else:
            print("value 1")
            return 1

    return '0'


def detect_port_loop():
    """ 
    This function detectes if there is a loop in the network ( more than 10 log in 2 seconds)

    :param:                         None
    :return int :                   If the int is equal to 1 we have detected a loop, if not the int equals 0
    """

    content_variable = open('/var/log/devices/lastlog_loop.json', 'r')
    file_lines = content_variable.readlines()
    content_variable.close()
    if len(file_lines) > 150:
        # clear lastlog file
        open('/var/log/devices/lastlog_loop.json', 'w', errors='ignore').close()

    if len(file_lines) >= 10:
        # check if the time of the last and the tenth last are less than seconds

        # first _ line
        first_line = file_lines[0].split(',')
        first_time = first_line[0]

        # last_line
        last_line = file_lines[9].split(',')
        last_time = last_line[0]

        # extract the timestamp (first_time and last_time)
        first_time_split = first_time[-len(first_time)+26:-7].split(':')
        last_time_split = last_time[-len(last_time)+26:-7].split(':')

        # time in hour into decimal of the first time : #else there is en error due to second  changes 60 to 0
        hour = first_time_split[0]
        # "%02d" %  force writing on 2 digits
        minute_deci = "%02d" % int(float(first_time_split[1])*100/60)
        second_deci = "%02d" % int(float(first_time_split[2])*100/60)
        first_time = "{0}{1}{2}".format(hour, minute_deci, second_deci)

        # time in hour into decimal of the last time : #else there is en error due to second  changes 60 to 0
        hour = last_time_split[0]
        # "%02d" %  force writing on 2 digits
        minute_deci = "%02d" % int(float(last_time_split[1])*100/60)
        second_deci = "%02d" % int(float(last_time_split[2])*100/60)
        last_time = "{0}{1}{2}".format(hour, minute_deci, second_deci)

        if(int(last_time)-int(first_time)) < 1:  # diff less than 2 seconds ( we can down to 1)
            return 1
        else:
            # clear lastlog file
            open('/var/log/devices/lastlog_loop.json',
                 'w', errors='ignore').close()
            return 0
    else:
        return 0


def check_timestamp():
    """ 
    This function provides the time between the last log and the current log .

    :param :                        None
    :return int diff_time:          This is the time gap between the last log and the current log.
    """
    # read time of the current log processed

    content_variable = open(
        '/var/log/devices/lastlog_loop.json', 'r', errors='ignore')
    file_lines = content_variable.readlines()
    content_variable.close()
    last_line = file_lines[0]
    f = last_line.split(',')

    timestamp_current = f[0]
    current_time = timestamp_current[-len(timestamp_current) +
                                     26:-7].replace(':', '')

    if not os.path.exists('/var/log/devices/logtemp.json'):
        open('/var/log/devices/logtemp.json', 'w', errors='ignore').close()

    # read time of the last log  processed
    f_lastlog = open('/var/log/devices/logtemp.json', 'r', errors='ignore')
    first_line = f_lastlog.readlines()

    # if logtemps is empty or more than 1 line in the file ( avoid error), clear the file
    if len(first_line) != 1:
        f_lastlog = open('/var/log/devices/logtemp.json', 'w', errors='ignore')
        f_lastlog.write(last_line)
        f_lastlog.close()

    f_lastlog_split = first_line[0].split(',')
    timestamp_last = f_lastlog_split[0]
    last_time = timestamp_last[-len(timestamp_last)+26:-7].replace(':', '')
    diff_time = int(current_time) - int(last_time)

    return diff_time

def isEssential(addr):
    """
    Check if IP addr is in Esssential_ip.csv file
    return: True if addr is in file else False
    """
    ips_address = list()
    with open("/opt/ALE_Script/Essential_ip.csv") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=';')
            line = 0
            for row in csv_reader:
                if line == 0:
                    line = 1
                    continue
                ips_address.append(str(row[0]))
    print(ips_address)
    for ip in ips_address:
        if ip == addr:
            return True
    return False

def isUpLink(switch_user, switch_password, port_number, ipadd):
    """
    Check if port is an Uplink (linkagg or more than 2 VLAN tagged)
    return: True if the port is considered as Uplink else False
    """
    l_switch_cmd = []
    l_switch_cmd.append("show  vlan members port " + port_number)

    for switch_cmd in l_switch_cmd:
        try:
            output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_vlan_members = output_decode.replace("['","")
                print(output_vlan_members)
            else:
                exception = "Timeout"
                info = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                os.system('logger -t montag -p user.info ' + info)
                send_message(info, jid)
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                except UnboundLocalError as error:
                    print(error)
                except Exception as error:
                    print(error)
                    pass 
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
        except subprocess.SubprocessError as exception:
            info = ("The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass 
            sys.exit()
        ## if port is member of a linkagg ERROR is displayed in output
        if re.search(r"ERROR", output_vlan_members):
            return True
        else:
        ## if port is member of more than 2 VLAN tagged
            qtagged = re.findall(r"qtagged", output)
            if len(qtagged) > 1:
                return True
            else:
                return False
        
def disable_port(user, password, ipadd, portnumber):
    """ 
    This function disables the port where there is a loop  on the switch put in arguments.

    :param str user:                Switch user login
    :param str password:            Switch user password
    :param str ipadd:               Switch IP Address
    :param str portnumber:          The Switch port where there is a loop. shape : x/y/z with x = chassis n ; y = slot n ; z = port n
    :return:                        None
    """
    cmd = "interfaces port {0} admin-state disable".format(portnumber)
    # ssh session to start python script remotely
    os.system('logger -t montag -p port disabling')
    os.system(
        "sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  {1}@{2} {3}".format(password, user, ipadd, cmd))
    os.system(
        'logger -t montag -p user.info Following port is administratively disabled: ' + portnumber)

def port_monitoring(switch_user, switch_password, port, ipadd):
    """ 
    This function executes a port monitoring (packet capture) on port received in argument  
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str port:                  Switch Interface/Port ID <chasis>/<slot>/>port>
    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
   ## Execute port monitoring on port with subprocess.call as we are not expecting output
    switch_cmd = ("port-monitoring 1 source port " + port + " file /flash/pmonitor.enc size 1 timeout 30 inport capture-type full enable")
    cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user, ipadd, switch_cmd)
    try:
        output = subprocess.call(cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
        print(output)
        return True
    except subprocess.SubprocessError:
        print("Issue when executing command")


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
    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_File_"+company
    request_debug = "Call VNA REST API Method POST path %s" % url
    print(request_debug)
    os.system('logger -t montag -p user.info Call VNA REST API Method POST')
    headers = {'Content-type': "text/plain", 
    'Content-Disposition': ("attachment;filename={0}_troubleshooting.log").format(category),
    'jid1': '{0}'.format(jid),
    'tata': '{0}'.format(subject),
    'toto': '{0}'.format(action),
    'tutu': '{0}'.format(result),
    'Card': '0',
    'Email': '0'}
    files = {'file': open(filename_path, 'r')}
    try:
        response = requests.post(url, files=files, headers=headers, timeout=20)
        code = re.findall(r"<Response \[(.*?)\]>", str(response))
        if "200" in code:
            os.system('logger -t montag -p user.info 200 OK')
            print("Response  Text from VNA")
            value = response.text
            print(value)
            print(code)
            try:
                write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No", "Decision": "Success"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass
        else:
            os.system('logger -t montag -p user.info REST API Timeout')
            pass
    except requests.exceptions.ConnectionError as response:
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
    except requests.exceptions.Timeout as response:
        print("Request Timeout when calling URL: " + url)
        print(response)
        try:
           write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
    except requests.exceptions.TooManyRedirects as response:
        print("Too Many Redirects when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass
    except requests.exceptions.RequestException as response:
        print("Request exception when calling URL: " + url)
        print(response)
        try:
            write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                "HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except Exception as error:
            print(error)
            pass



if __name__ == "__main__":
#    a = isUpLink("admin", "switch", "1/1/21", "10.130.7.239")
#    print(a)
#    b = isEssential("10.130.7.14")
#    print(b)
    login_switch, pass_switch, mails, rainbow_jid, ip_server_log, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()
    jid = "570e12872d768e9b52a8b975@openrainbow.com"
    switch_password = "switch"
    switch_user = "admin"
    ipadd = "10.130.7.244"
    cmd = "show system"
    host = "LAN-6860N-2"
    port = "1/1/52"
    source = "Unknown Unicast"
    decision = 0
#    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
#    filename_path, subject, action, result, category = get_tech_support_sftp(switch_user, switch_password, host, ipadd)
    filename_path, subject, action, result, category, chassis_id = collect_command_output_fan(switch_user, switch_password, host, ipadd)
    send_file(filename_path, subject, action, result, category)
#    filename_path, subject, action, result, category = collect_command_output_network_loop(switch_user, switch_password, ipadd, port)
#    send_file(filename_path, subject, action, result,category)
    filename_path, subject, action, result, category = collect_command_output_storm(switch_user, switch_password, port, source, decision, host, ipadd)
    send_file(filename_path, subject, action, result,category)
    reason="Fail due to out-of-range capacitor value"
    port="34"
    filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status = collect_command_output_poe(switch_user, switch_password, host, ipadd, port, reason)
    send_file(filename_path, subject, action, result,category)
    agg = "6"
    filename_path, subject, action, result, category = collect_command_output_linkagg(switch_user, switch_password, agg, host, ipadd)
    send_file(filename_path, subject, action, result,category)
    vcid = "2"
    filename_path, subject, action, result, category = collect_command_output_vc(switch_user, switch_password, vcid, host, ipadd)
    send_file(filename_path, subject, action, result,category)
    psid = "2"
    filename_path, subject, action, result, category = collect_command_output_ps(switch_user, switch_password, psid, host, ipadd)
    send_file(filename_path, subject, action, result,category)
    source = "Access Guardian"

    decision = "0"
    filename_path, subject, action, result, category = collect_command_output_violation(switch_user, switch_password, port, source, decision, host, ipadd)
    send_file(filename_path, subject, action, result,category)
    filename_path, subject, action, result, category = collect_command_output_storm(switch_user, switch_password, port, source, decision, host, ipadd)
    send_file(filename_path, subject, action, result,category)
    protocol = "HTTPS"
    user = "toto"
    source_ip = "10.130.7.17"
    service_status, aaa_status = collect_command_output_aaa(switch_user, switch_password, protocol, ipadd)
    filename_path, subject, action, result, category = authentication_failure(switch_user, switch_password, user, source_ip, protocol, service_status, aaa_status, host, ipadd)
    send_file(filename_path, subject, action, result,category)

else:
    print("Support_Tools_OmniSwitch Script called by another script")
