#!/usr/local/bin/python3.7

from ast import And
#from asyncio.base_events import _ExceptionHandler
from asyncio.subprocess import PIPE
#from asyncore import compact_traceback
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
from support_send_notification import *
import subprocess
import re
import requests
import paramiko
import csv
import threading
from database_conf import *
import traceback
import syslog

syslog.openlog('support_tools_OmniSwitch')

# This script contains all functions interacting with OmniSwitches

# Function for extracting environment information from ALE_script.conf file

dir="/opt/ALE_Script"
attachment_path = "/var/log/server/log_attachment"

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

    with open(dir + "/ALE_script.conf", "r") as content_variable:
        login_switch, pass_switch, mails, rainbow_jid1, rainbow_jid2, rainbow_jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company, room_id, * \
            kargs = re.findall(
                r"(?:,|\n|^)(\"(?:(?:\"\")*[^\"]*)*\"|[^\",\n]*|(?:\n|$))", str(content_variable.read()))
        if attribute == None:
            return login_switch, pass_switch, mails, rainbow_jid1, rainbow_jid2, rainbow_jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company
        elif attribute == "login_switch":
            return login_switch
        elif attribute == "pass_switch":
            return pass_switch
        elif attribute == "mails":
            return mails
        elif attribute == "rainbow_jid":
            return [rainbow_jid1, rainbow_jid2, rainbow_jid3]
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


switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

# Function used to pass command remotely in different shell like bshell
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
    exception = output = 0
    print("Function ssh_connectivity_check - we execute command " + cmd + " on Device: " + ipadd)
    syslog.syslog(syslog.LOG_INFO, "------------------------------")
    syslog.syslog(syslog.LOG_INFO, "Function ssh_connectivity_check - we execute command " + cmd + " on Device " + ipadd)
    syslog.syslog(syslog.LOG_INFO, "------------------------------")
    cmd = str(cmd)
    try:
        p = paramiko.SSHClient()
        p.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        syslog.syslog(syslog.LOG_INFO, "SSH Session start")
        p.connect(ipadd, port=22, username=switch_user,password=switch_password, timeout=20.0, banner_timeout=100)
        syslog.syslog(syslog.LOG_INFO, "SSH Session established")
    except TimeoutError as exception:
        syslog.syslog(syslog.LOG_DEBUG, "{0!s}".format(traceback.format_exc(chain=False,limit=None).encode("utf-8")))
        exception = "SSH Timeout"
        syslog.syslog(syslog.LOG_INFO, "Exception: " + str(exception))
        print("Function ssh_connectivity_check - Exception: " + str(exception))
        print("Function ssh_connectivity_check - Timeout when establishing SSH Session")
        notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message_detailed(notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "Timed out", "IP_Address": ipadd}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as exception:
            print(str(exception)) 
        except Exception as exception:
            print(str(exception))
        #syslog.syslog(syslog.LOG_INFO, "Script exit")
        #os._exit(1)
        return output, exception
    except paramiko.AuthenticationException as exception:
        syslog.syslog(syslog.LOG_DEBUG, "{0!s}".format(traceback.format_exc(chain=False,limit=None).encode("utf-8")))
        exception = "AuthenticationException"
        syslog.syslog(syslog.LOG_INFO, "Exception: " + str(exception))
        print("Function ssh_connectivity_check - Authentication failed enter valid user name and password")
        notif = ("SSH Authentication failed when connecting to OmniSwitch {0}, we cannot collect logs or proceed for remediation action").format(ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message_detailed(notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "AuthenticationException", "IP_Address": ipadd}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as exception:
            print(str(exception))
            return exception 
        except Exception as exception:
            print(str(exception))
            return exception 
        syslog.syslog(syslog.LOG_INFO, "Script exit")
        os._exit(1)
    except (paramiko.SSHException,ConnectionError) as exception:
        syslog.syslog(syslog.LOG_DEBUG, "{0!s}".format(traceback.format_exc(chain=False,limit=None).encode("utf-8")))
        syslog.syslog(syslog.LOG_INFO, "Exception: " + str(exception))
        print("Function ssh_connectivity_check - " + str(exception))
        #exception = exception.readlines()
        exception = str(exception)
        print("Function ssh_connectivity_check - Device unreachable")
        syslog.syslog(syslog.LOG_INFO, " SSH session does not establish on OmniSwitch " + ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        notif = ("OmniSwitch {0} is unreachable, we cannot collect logs").format(ipadd)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message_detailed(notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "DeviceUnreachable", "IP_Address": ipadd}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as exception:
            print(str(exception))
            return exception
        except Exception as exception:
            print(str(exception))
            return exception
        syslog.syslog(syslog.LOG_INFO, "Script exit")
        os._exit(1)
    except Exception as exception:
        syslog.syslog(syslog.LOG_DEBUG, "{0!s}".format(traceback.format_exc(chain=False,limit=None).encode("utf-8")))
        syslog.syslog(syslog.LOG_INFO, "Exception: " + str(exception))
        print("Function ssh_connectivity_check - " + str(exception))
        #exception = exception.readlines()
        exception = str(exception)
        print("Function ssh_connectivity_check - Device unreachable")
        logging.info(' SSH session does not establish on OmniSwitch ' + ipadd)
        notif = ("OmniSwitch {0} is unreachable, we cannot collect logs").format(ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)        
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message_detailed(notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "DeviceUnreachable", "IP_Address": ipadd}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as exception:
            print(str(exception))
            return exception
        except Exception as exception:
            print(str(exception))
            return exception
        syslog.syslog(syslog.LOG_INFO, "Script exit")
        os._exit(1)
    try:
        stderr = ""
        stdout = ""
        stdin = ""
        #syslog.syslog(syslog.LOG_INFO, "SSH Command Execution: " + cmd)
        stdin, stdout, stderr = p.exec_command(cmd, timeout=120)
        print(stdout)
        syslog.syslog(syslog.LOG_INFO, "SSH Command stdout: " + stdout)
        print(stderr)
        syslog.syslog(syslog.LOG_INFO, "SSH Command stdout: " + stderr)
    except AttributeError as exception:
        pass
    except TypeError as exception:
        pass
    except paramiko.SSHException as exception:
        syslog.syslog(syslog.LOG_DEBUG, "{0!s}".format(traceback.format_exc(chain=False,limit=None).encode("utf-8")))
        print(str(exception))
        syslog.syslog(syslog.LOG_INFO, "Exception: " + str(exception))
        pass
 #   except Exception as exception:
        #exception = "SSH Exception"
 #       syslog.syslog(syslog.LOG_INFO, "Exception: " + str(exception))
 #       print("Function ssh_connectivity_check - " + str(exception))
 #       notif = ("Command {0} execution on OmniSwitch {1} failed - {2}").format(switch_cmd,ipadd, exception)
        
 #       syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
 #       send_message_detailed(notif)
  #      syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
  #      try:
  #          write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
 #           syslog.syslog(syslog.LOG_INFO, "Statistics saved")
  #      except UnboundLocalError as exception:
 #           print(exception)
  #          return exception
#        except Exception as exception:
 #           print(exception)
  #          os._exit(1)
   
    try:
        exception = stderr.readlines()
        exception = str(exception)
        connection_status = stdout.channel.recv_exit_status()
    except:
        connection_status = 1
    print(connection_status)
    print(exception)
    if connection_status != 0:
        notif = ("Command {0} execution on OmniSwitch {1} failed - {2}").format(cmd,ipadd, exception)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message_detailed(notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as exception:
            print(exception)
            return exception
        except Exception as exception:
            print(exception)
            return exception 
    else:
        notif = ("SSH Session established successfully on OmniSwitch {0}").format(ipadd)
        syslog.syslog(syslog.LOG_INFO, "SSH Session established successfully on OmniSwitch " + ipadd +  " and command " + cmd + " passed")
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_success", "tags": {"IP_Address": ipadd}, "fields": {"count": 1}}])
            syslog.syslog(syslog.LOG_INFO, "Statistics saved")
        except UnboundLocalError as exception:
            print(exception)
            return exception
        except Exception as exception:
            print(exception)
            return exception
        try:
            output = stdout.readlines()
        except UnicodeDecodeError as exception:
            syslog.syslog(syslog.LOG_DEBUG, "{0!s}".format(traceback.format_exc(chain=False,limit=None).encode("utf-8")))
            syslog.syslog(syslog.LOG_INFO, "Exception: " + str(exception))
            raise       
        # We close SSH Session once retrieved command output
        p.close()
        syslog.syslog(syslog.LOG_INFO, "SSH Session End")
        return output, exception

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
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function get_file_sftp")
    syslog.syslog(syslog.LOG_INFO, "    ")
    date = datetime.date.today()
    syslog.syslog(syslog.LOG_INFO, "SSH Session start")
    ssh = paramiko.SSHClient()
    print(remoteFilePath)
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ipadd, username=switch_user,password=switch_password, timeout=10.0)
        syslog.syslog(syslog.LOG_INFO, "SSH Session established")
        sftp = ssh.open_sftp()
        # In case of SFTP Get timeout thread is closed and going into Exception
        try:
            syslog.syslog(syslog.LOG_INFO, "SFTP get file " + remoteFilePath + " on local directory " + localFilePath)
            th = threading.Thread(target=sftp.get, args=(remoteFilePath, localFilePath))
            th.start()
            th.join(60)
        except threading.ThreadError as exception:
            syslog.syslog(syslog.LOG_DEBUG, "{0!s}".format(traceback.format_exc(chain=False,limit=None).encode("utf-8")))
            print(exception)
            syslog.syslog(syslog.LOG_INFO, "SFTP Session aborted reason: " + exception)
            pass
        except FileNotFoundError as exception:
            syslog.syslog(syslog.LOG_DEBUG, "{0!s}".format(traceback.format_exc(chain=False,limit=None).encode("utf-8")))
            print(exception)
            syslog.syslog(syslog.LOG_INFO, "Remote file not found: " + exception)
            pass          
    except TimeoutError as exception:
        syslog.syslog(syslog.LOG_DEBUG, "{0!s}".format(traceback.format_exc(chain=False,limit=None).encode("utf-8")))
        exception = "SSH Timeout"
        syslog.syslog(syslog.LOG_INFO, "Exception: " + str(exception))
        print("Function ssh_connectivity_check - Exception: " + str(exception))
        print("Function ssh_connectivity_check - Timeout when establishing SSH Session")
        notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message_detailed(notif)
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
        syslog.syslog(syslog.LOG_DEBUG, "{0!s}".format(traceback.format_exc(chain=False,limit=None).encode("utf-8")))
        exception = "AuthenticationException"
        syslog.syslog(syslog.LOG_INFO, "Exception: " + str(exception))
        print("Function ssh_connectivity_check - Authentication failed enter valid user name and password")
        notif = ("SSH Authentication failed when connecting to OmniSwitch {0}, we cannot collect logs or proceed for remediation action").format(ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message_detailed(notif)
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
        pass
    except paramiko.SSHException as error:
        syslog.syslog(syslog.LOG_DEBUG, "{0!s}".format(traceback.format_exc(chain=False,limit=None).encode("utf-8")))
        syslog.syslog(syslog.LOG_INFO, "Exception: " + str(exception))
        print("Function ssh_connectivity_check - " + str(exception))
        #exception = exception.readlines()
        exception = str(exception)
        print("Function ssh_connectivity_check - Device unreachable")
        syslog.syslog(syslog.LOG_INFO, " SSH session does not establish on OmniSwitch " + ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        notif = ("OmniSwitch {0} is unreachable, we cannot collect logs").format(ipadd)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message_detailed(notif)
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
        ssh.close()
        syslog.syslog(syslog.LOG_INFO, "SSH Session end")
        syslog.syslog(syslog.LOG_INFO, "Script exit")  
        os._exit(1)
    ssh.close()


def format_mac(mac):
    """ 
    This function for removing delimiters and convert MAC Address into lower case
    We extract from syslog message the pmd file path and we download with python sftp client
    :param str mac            Attacker's MAC Address
    :return:  mac                  
    """
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function format_mac")
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "MAC received: " + mac)
    # remove delimiters and convert to lower case
    mac = re.sub('[.:-]', '', mac).lower()
    mac = ''.join(mac.split())  # remove whitespaces
    syslog.syslog(syslog.LOG_INFO, "MAC with new format: " + mac)
    assert len(mac) == 12  # length should be now exactly 12 (eg. 008041aefd7e)
    assert mac.isalnum()  # should only contain letters and numbers
    # convert mac in canonical form (eg. 00:80:41:ae:fd:7e)
    mac = ":".join(["%s" % (mac[i:i+2]) for i in range(0, 12, 2)])
    syslog.syslog(syslog.LOG_INFO, "MAC in canonical format: " + mac)
    return mac


def file_setup_qos(addr):
    """ 
    This function takes as argument the IP or MAC Address of the Attacker and fil-in the configqos file for applying the Policy Rule to prevent access to the network
    We extract from syslog message the pmd file path and we download with python sftp client
    :param str addr            IP or MAC Address of the Attacker
    """
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function file_setup_qos")
    syslog.syslog(syslog.LOG_INFO, "    ")
    content_variable = open(dir + '/configqos', 'w')
    if re.search(r"\:", addr):  # mac
        syslog.syslog(syslog.LOG_INFO, "If MAC Address contains : as delimiters")
        setup_config = "policy condition scanner_{0} source mac {0}\npolicy action block_mac disposition deny\npolicy rule scanner_{0} condition scanner_{0} action block_mac\nqos apply\nqos enable\n".format(addr)
        syslog.syslog(syslog.LOG_INFO, "configqos File Content: " + str(setup_config))
    else:
        setup_config = "policy condition scanner_{0} source ip {0}\npolicy action block_ip disposition deny\npolicy rule scanner_{0} condition scanner_{0} action block_ip\nqos apply".format(addr)
        syslog.syslog(syslog.LOG_INFO, "configqos File Content: " + str(setup_config))
    content_variable.write(setup_config)
    content_variable.close()

# Function to enable syslogs on OmniSwitches when Setup.sh is called
def enable_syslog(switch_user, switch_password, ipadd, port, server_ip):
    """ 
    This function takes entries arguments the OmniSwitch IP Address from Devices.csv file, the OmniSwitch credentials, the syslog port to be used
    Note that VRF is not supported, syslog are enabled on the default VRF

    :param str ipadd:                 OmniSwitch IP Address
    :param str server_ip:             Preventive Maintenance Server IP Address
    :param str port:                  Syslog Port (default 10514)
    :script executed ssh_device:      with cmd in argument
    :return:                          None
    """
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function enable_syslog")
    syslog.syslog(syslog.LOG_INFO, "    ")
    cmd = ("swlog output socket {0} {1}").format(server_ip, port)
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)

# Function debug enable or disable
def debugging(switch_user, switch_password, ipadd, appid, subapp, level):
    """ 
    This function takes entries arguments the appid, subapp and level to apply on OmniSwitch for enabling (level debug1, debug2) or disabling debug logs (level info)

    :param str appid_1:               swlog appid function (ipv4,bcmd)
    :param str subapp_1:              swlog subapp component (all)
    :param str level_1:               swlog debug level (debug1,debug2,debug3,info)
    :script executed ssh_device:      with cmd in argument
    :return:                          None
    """
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function debugging")
    syslog.syslog(syslog.LOG_INFO, "    ")
    cmd = ("swlog appid {0} subapp {1} level {2}").format(appid, subapp, level)
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)


def enable_port(switch_user, switch_password, ipadd, portnumber):
    """ 
    This function enables the port where there is a loop detected on the OmniSwitch put in arguments.
    :param str user:                Switch user login
    :param str password:            Switch user password
    :param str ipadd:               Switch IP Address
    :param str portnumber:          The Switch port where there is a loop. shape : x/y/z with x = chassis n ; y = slot n ; z = port n
    :return:                        None
    """
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function enable_port")
    syslog.syslog(syslog.LOG_INFO, "    ")
    cmd = "interfaces port {0} admin-state enable".format(portnumber)
    # ssh session to start python script remotely
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
    syslog.syslog(syslog.LOG_INFO, "Following port is administratively enabled: " + portnumber)

# Function to collect tech_support_complete.tar file by SFTP
def get_tech_support_sftp(switch_user, switch_password, host, ipadd):
    """ 
    This function takes entries arguments the OmniSwitch IP Address
    This function returns file path containing the tech_support_complete file and the notification subject, body used when calling VNA API

    :param str host:                        Switch Hostname
    :param str ipadd:                       Switch IP address
    :return:                                filename_path,subject,action,result,category
    """
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function get_tech_support_sftp")
    syslog.syslog(syslog.LOG_INFO, "    ")
    date = datetime.date.today()
    date_hm = datetime.datetime.today()
    filename = 'tech_support_complete.tar'
    try:
        p = paramiko.SSHClient()
        p.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        p.connect(ipadd, port=22, username=switch_user, password=switch_password, timeout=10.0)
    except TimeoutError as exception:
        exception = "SSH Timeout"
        syslog.syslog(syslog.LOG_INFO, "Exception: " + str(exception))
        print("Function ssh_connectivity_check - Exception: " + str(exception))
        print("Function ssh_connectivity_check - Timeout when establishing SSH Session")
        notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message_detailed(notif)
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
            notif = ("SSH Authentication failed when connecting to OmniSwitch {0}, we cannot collect logs or proceed for remediation action").format(ipadd)
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
            send_message_detailed(notif)
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
    except paramiko.SSHException as error:
        syslog.syslog(syslog.LOG_INFO, "Exception: " + str(exception))
        print("Function ssh_connectivity_check - " + str(exception))
        #exception = exception.readlines()
        exception = str(exception)
        print("Function ssh_connectivity_check - Device unreachable")
        syslog.syslog(syslog.LOG_INFO, " SSH session does not establish on OmniSwitch " + ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        notif = ("OmniSwitch {0} is unreachable, we cannot collect logs").format(ipadd)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message_detailed(notif)
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
    stdin = ""
    stderr = ""
    stdout = ""
    syslog.syslog(syslog.LOG_INFO, "Removing existing snapshot logs")
    cmd = ("rm -rf {0}").format(filename)
    stdin, stdout, stderr = p.exec_command(cmd)
    exception = stderr.readlines()
    exception = str(exception)
    connection_status = stdout.channel.recv_exit_status()
    if connection_status != 0:
        notif = ("Command {0} execution on OmniSwitch {1} failed - {2}").format(cmd,ipadd, exception)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message_detailed(notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(str(error))
        except Exception as error:
            print(str(error))
            pass 
        os._exit(1)

    stdin, stdout, stderr = p.exec_command("show tech-support eng complete")
    exception = stderr.readlines()
    exception = str(exception)
    connection_status = stdout.channel.recv_exit_status()
    if connection_status != 0:
        notif = ("\"The show tech support eng complete\" command on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message_detailed(notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
        try:
            write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
        except UnboundLocalError as error:
            print(str(error))
        except Exception as error:
            print(str(error))
            pass 
        os._exit(1)

    cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2}  ls | grep {3}".format(
        switch_password, switch_user, ipadd, filename)
    run = cmd.split()
    stdout = ''
    i = 0
    while not stdout:
        print(" Tech Support file creation under progress.", end="\r")
        syslog.syslog(syslog.LOG_INFO, "Tech Support file creation under progress.")
        sleep(3)
        print(" Tech Support file creation under progress..", end="\r")
        syslog.syslog(syslog.LOG_INFO, "Tech Support file creation under progress..")
        sleep(3)
        print(" Tech Support file creation under progress...", end="\r")
        syslog.syslog(syslog.LOG_INFO, "Tech Support file creation under progress...")
        #print(i)
        sleep(3)
        print(" Tech Support file creation under progress....", end="\r")
        syslog.syslog(syslog.LOG_INFO, "Tech Support file creation under progress....")
        sleep(3)
        p = subprocess.Popen(run, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        stdout = stdout.decode('UTF-8').strip()
        if i > 20:
            print("Tech Support file creation timeout")
            syslog.syslog(syslog.LOG_INFO, "Tech Support file creation timeout - script exit")
            os._exit(1)

    filename = "tech_support_complete.tar"
    remoteFilePath = "./tech_support_complete.tar"
    localFilePath = "/tftpboot/{0}_{1}-{2}_{3}_{4}".format(date,date_hm.hour,date_hm.minute,ipadd,filename)
    #### SFTP GET tech support #####
    syslog.syslog(syslog.LOG_INFO, "SFTP get file " + remoteFilePath + " on local directory " + localFilePath)
    get_file_sftp(switch_user, switch_password, ipadd, remoteFilePath, localFilePath)
    print(localFilePath) #/tftpboot/2022-03-24_18-41_10.130.7.246_tech_support_complete.tar
    subject = ("Preventive Maintenance Application - Show Tech-Support Complete command executed on OmniSwitch: {0}").format(ipadd)
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
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_tcam")
    syslog.syslog(syslog.LOG_INFO, "    ")
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show qos config; show qos statistics; show qos log; show qos rules; show tcam utilization detail")

    for switch_cmd in l_switch_cmd:
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
                notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
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

    filename = "{0}_{1}-{2}_{3}_tcam_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (attachment_path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - A TCAM failure (QOS) is noticed on OmniSwitch: {0}, reason {1}").format(ipadd, source)
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
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_network_loop")
    syslog.syslog(syslog.LOG_INFO, "    ")
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append(("show system; show chassis; show interfaces {0} status; show mac-learning port {0}; show vlan members port {0}").format(port))      

    for switch_cmd in l_switch_cmd:
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
                notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
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

    filename = "{0}_{1}-{2}_{3}_network_loop_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (attachment_path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - A loop has been detected on your network and the port {0} is administratively disabled on device {1}").format(port,ipadd)
    action = ("A Network Loop is noticed on OmniSwitch: {0} and we have deactivated the interface administratively").format(ipadd)
    result = ("Find enclosed to this notification the log collection of last 5 minutes and interface port {0} status. More details in the Technical Knowledge Base https://myportal.al-enterprise.com/alebp/s/tkc-redirect?000051875").format(port)
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
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_ovc")
    syslog.syslog(syslog.LOG_INFO, "    ")
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show system; show cloud-agent status; show cloud-agent vpn status; show ntp server status; show log swlog | grep 'openvpn\|ovcCmm'; cat libcurl_log")

    if vpn_ip != "0":
        syslog.syslog(syslog.LOG_INFO, "VPN IP Address received " + vpn_ip)
        l_switch_cmd.append(("ping {0}; traceroute {0} max-hop 3").format(vpn_ip))

    for switch_cmd in l_switch_cmd:
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
                notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
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

    filename = "{0}_{1}-{2}_{3}_ovc_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (attachment_path + '/{0}.txt').format(filename)
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
    elif reason == "Fatal TLS error":
        subject = ("Preventive Maintenance Application - OVC Activation Server is unreachable from OmniSwitch {0} reason - TLS Handshake failed").format(host)
        action = ("The VPN Interface is DOWN on OmniSwitch (Hostname: {0}), TLS key negotiation failed please check your Network connectivity").format(host)
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
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_mqtt")
    syslog.syslog(syslog.LOG_INFO, "    ")
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show device-profile config; show appmgr iot-profiler")

    for switch_cmd in l_switch_cmd:
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
                notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
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

    filename = "{0}_{1}-{2}_{3}_mqtt_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (attachment_path + '/{0}.txt').format(filename)
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
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_storm")
    syslog.syslog(syslog.LOG_INFO, "    ")
    ## Log collection of additionnal command outputs
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append(("show health port {0} ; show interfaces {0}; sleep 2 ; show interfaces {0}; sleep 2 ;\
    show interfaces {0}; sleep 2;  show interfaces {0} flood-rate").format(port))

    if decision == "1" or decision == "2":
        l_switch_cmd.append("interfaces port " + port + " admin-state disable")
    for switch_cmd in l_switch_cmd:
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
                notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
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

    filename = "{0}_{1}-{2}_{3}_storm_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (attachment_path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - Unexpected traffic (storm) detected on OmniSwitch: {0}, reason {1}").format(ipadd, source)
    if decision == "1" or decision == "2":
        action = ("The Interface {0} is administratively disabled on OmniSwitch (Hostname: {1})").format(port, host)
        result = "Find enclosed to this notification the log collection of actions done. More details in the Technical Knowledge Base https://myportal.al-enterprise.com/alebp/s/tkc-redirect?000061786"
    else:
        action = ("No action done on OmniSwitch (Hostname: {0})").format(host)
        result = "Find enclosed to this notification the interface's status/statistics"
    category = "storm"
    return filename_path, subject, action, result, category

def collect_command_output_flapping(switch_user, switch_password, port, ipadd):
    """ 
    This function takes entries arguments the Interface/Port where flapping occurs and the type of traffic. 
    This function checks the decision received from Admin:
       if decision is 1, Administrator selected Yes and script disables the interface
       if decision is 0, Administrator selected No and we only provide command outputs  
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str port:                  Switch Interface/Port ID <chasis>/<slot>/>port>
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_flapping")
    syslog.syslog(syslog.LOG_INFO, "    ")
    ## Log collection of additionnal command outputs
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append(("show interfaces port {0}").format(port))
    status_changes = link_quality = ""
    for switch_cmd in l_switch_cmd:
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
                notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
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
            try:
                status_changes = re.findall(r"Number of Status Change   : (.*?),", output_decode)[0]
            except IndexError:
                print("Index error in regex")
                syslog.syslog(syslog.LOG_INFO, "Index error in regex for status_changes")
            try:
                link_quality = re.findall(r"Link-Quality              : (.*?),", output_decode)[0]
            except IndexError:
                print("Index error in regex")
                syslog.syslog(syslog.LOG_INFO, "Index error in regex for link_quality")
    return status_changes, link_quality


# Function to collect several command outputs related to High CPU detected
def collect_command_output_health_cpu(switch_user, switch_password, host, ipadd):
    """ 
    This function takes entries arguments the Switch IPAddress/Hostname where High CPU occurs 
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_health_cpu")
    syslog.syslog(syslog.LOG_INFO, "    ")
    ## Log collection of additionnal command outputs
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show virtual-chassis topology; show chassis; show system; show health; show health all cpu; show health all memory; show health all rx; show health all txrx")
    l_switch_cmd.append('echo \"top -d 5 -n 5\" | su ; echo \"free -m\" | su \
        ; sleep 2 ; echo \"free -m\" | su ; echo \"top -b -n 1 | head\" | su \
        ; echo \"top -b -n 1 | head\" | su ; sleep 2 ; echo \"top -b -n 1 | head\" | su \
        ; sleep 2 ; echo \"top -b -n 1 | head\" | su ; sleep 2 ; echo \"top -b -n 1 | head\" | su \
        ; sleep 2 ; echo \"top -b -n 1 | head\" | su')

    for switch_cmd in l_switch_cmd:
            output, exception = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
            if exception != None:
                notif = ("Preventive Maintenance Application - We detected an High CPU on OmniSwitch {0}/{1}. We are not able to collect logs - reason: Timeout when establishing SSH Session to OmniSwitch {1}").format(host,ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
                syslog.syslog(syslog.LOG_INFO, "Script exit")
                os._exit(1)    
            elif output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output_decode)
            else:
                exception = "Timeout"
                notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                    syslog.syslog(syslog.LOG_INFO, "Statistics saved")
                except UnboundLocalError as error:
                    print(str(error))
                except Exception as error:
                    print(str(error))
                    pass
                syslog.syslog(syslog.LOG_INFO, "Script exit") 
                os._exit(1)
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_health_cpu_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (attachment_path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - High CPU issue detected on OmniSwitch: {0}").format(ipadd)
    action = ("A High CPU issue has been detected on OmniSwitch( Hostname: {0} ) and we have collected logs as well as Tech-Support eng complete archive").format(host)
    result = "Find enclosed to this notification the log collection for further analysis"
    category = "health_cpu"
    return filename_path, subject, action, result, category

# Function to collect several command outputs related to High Memory detected
def collect_command_output_health_memory(switch_user, switch_password, host, ipadd):
    """ 
    This function takes entries arguments the Switch IPAddress/Hostname where High Memory occurs 
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_health_memory")
    syslog.syslog(syslog.LOG_INFO, "    ")
    ## Log collection of additionnal command outputs
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show virtual-chassis topology; show chassis; show system; show health; show health all cpu; show health all memory; show health all rx; show health all txrx")
    l_switch_cmd.append('echo \"top -d 5 -n 5\" | su ; echo \"free -m\" | su \
        ; sleep 2 ; echo \"free -m\" | su ; echo \"top -b -n 1 | head\" | su \
        ; echo \"top -b -n 1 | head\" | su ; sleep 2 ; echo \"top -b -n 1 | head\" | su \
        ; sleep 2 ; echo \"top -b -n 1 | head\" | su ; sleep 2 & echo \"top -b -n 1 | head\" | su \
        ; sleep 2 ; echo \"top -b -n 1 | head\" | su ; echo \"cat \/proc\/meminfo\" | su \
        ; sleep 2 ; echo \"cat \/proc\/meminfo\" | su')

    for switch_cmd in l_switch_cmd:
            output, exception = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
            if exception != None:
                notif = ("Preventive Maintenance Application - We detected an High Memory on OmniSwitch {0}/{1}. We are not able to collect logs - reason: Timeout when establishing SSH Session to OmniSwitch {1}").format(host,ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
                syslog.syslog(syslog.LOG_INFO, "Script exit")
                os._exit(1)    
            elif output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output_decode)
            else:
                exception = "Timeout"
                notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
                try:
                    write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ipadd, "Exception": exception}, "fields": {"count": 1}}])
                    syslog.syslog(syslog.LOG_INFO, "Statistics saved")
                except UnboundLocalError as error:
                    print(str(error))
                except Exception as error:
                    print(str(error))
                    pass
                syslog.syslog(syslog.LOG_INFO, "Script exit") 
                os._exit(1)
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_health_memory_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (attachment_path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - High Memory issue detected on OmniSwitch: {0}").format(ipadd)
    action = ("A High Memory issue has been detected on OmniSwitch( Hostname: {0} ) and we have collected logs as well as Tech-Support eng complete archive").format(host)
    result = "Find enclosed to this notification the log collection for further analysis"
    category = "health_memory"
    return filename_path, subject, action, result, category

# Function to collect several command outputs related to High Consumption on port detected
def collect_command_output_health_port(switch_user, switch_password, port, type, host, ipadd):
    """ 
    This function takes entries arguments the Switch IPAddress/Hostname where High consumption on port is noticed
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str port:                  Switch Interface/Port number where RMON noticed traffic above threshold
    :param str type:                  Switch RMON type receive or receive/transmit
    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_health_port")
    syslog.syslog(syslog.LOG_INFO, "    ")
    ## Log collection of additionnal command outputs
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append(("show virtual-chassis topology; show chassis; show system; show health; show interfaces flood-rate; \
    show health port {0} ; show qos port {0}").format(port))

    for switch_cmd in l_switch_cmd:
            output, exception = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
            if exception != None:
                notif = ("Preventive Maintenance Application - We detected an High consumption on port {0} on OmniSwitch {1}/{2}. We are not able to collect logs - reason: Timeout when establishing SSH Session to OmniSwitch {2}").format(port,host,ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
                syslog.syslog(syslog.LOG_INFO, "Script exit")
                os._exit(1)               
            elif output != None or output != 0:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '","")
                output_decode = output_decode.replace("']","")
                output_decode = output_decode.replace("['","")
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output_decode)
            else:
                exception = "Timeout"
                notif = ("Preventive Maintenance Application - We detected an High consumption on port {0} on OmniSwitch {1}/{2}. We are not able to collect logs - reason: Timeout when establishing SSH Session to OmniSwitch {2}").format(port,host,ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Notification sent")
                syslog.syslog(syslog.LOG_INFO, "Script exit")
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

    filename = "{0}_{1}-{2}_{3}_health_port_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (attachment_path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - High Consumption detected on on OmniSwitch: {0} port {1}").format(ipadd, port)
    action = ("A High Traffic has been detected on OmniSwitch( Hostname: {0} ), port {1} of type {2} and we have collected logs").format(host, port, type)
    result = "Find enclosed to this notification the log collection for further analysis"
    category = "health_port"
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
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_violation")
    syslog.syslog(syslog.LOG_INFO, "    ")
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    if decision == "1":
        l_switch_cmd.append(("show interfaces {0} status ; clear violation port {0} ; show violation; show violation port {0}").format(port))
    else:
        l_switch_cmd.append(("show interfaces {0} status ; show violation; show violation port {0}").format(port))

    for switch_cmd in l_switch_cmd:
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
                notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
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

    filename = "{0}_{1}-{2}_{3}_violation_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (attachment_path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - Port violation noticed on OmniSwitch: {0}, reason {1}").format(ipadd, source)
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
def collect_command_output_spb(switch_user, switch_password, host, ipadd, adjacency_id, port):
    """ 
    This function takes entries arguments the OmniSwitch IP Address
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :param str adjacency_id:          Switch SPB System ID
    :param str port:                  Switch Port where Adjacency is lost
    :return:                          filename_path,subject,action,result,category
    """
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_spb")
    syslog.syslog(syslog.LOG_INFO, "    ")
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show spb isis info; show spb isis database; show spb isis adjacency; show spb isis interface")

    for switch_cmd in l_switch_cmd:
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
                notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
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

    filename = "{0}_{1}-{2}_{3}_spb_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (attachment_path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - SPB Adjacency issue detected on OmniSwitch: {0}").format(ipadd)
    action = ("Preventive Maintenance Application - SPB Adjacency state change on OmniSwitch {0} / {1}. System ID : {2} - Port : {3}. Please check the SPB Adjacent node connectivity.").format(host,ipadd,adjacency_id,port)
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
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_stp")
    syslog.syslog(syslog.LOG_INFO, "    ")
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    if decision == "1":
        l_switch_cmd.append(("show microcode; show system; show spantree mode; show spantree vlan {0}; show vlan {0}; spantree vlan {0} admin-state enable; show spantree vlan {0}").format(vlan))
    else:
        l_switch_cmd.append(("show microcode; show system; show spantree mode; show spantree vlan {0}; show vlan {0}; show spantree vlan {0}").format(vlan))
  
    for switch_cmd in l_switch_cmd:
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
                notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
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

    filename = "{0}_{1}-{2}_{3}_stp_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (attachment_path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()

    subject = ("Preventive Maintenance Application - STP configuration issue detected on OmniSwitch: {0} / {1}").format(host,ipadd)
    if decision == "1":
        action = ("Decision set to Yes. The Spanning Tree on VLAN {0} is enabled on OmniSwitch (Hostname: {1})").format(vlan,host)
        result = "Find enclosed to this notification the log collection for further analysis"
    else:
        action = ("The Spanning Tree on VLAN {0} is not enabled on OmniSwitch (Hostname: {1})").format(vlan,host)
        result = "Find enclosed to this notification the log collection for further analysis"       
    category = "stp"
    return filename_path, subject, action, result, category


# Function to collect several command outputs related to FAN failure
def collect_command_output_fan(switch_user, switch_password, fan_id, host, ipadd):
    """ 
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str fan_id:                FAN Unit Identifier
    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category, chassis_id
    """
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_fan")
    syslog.syslog(syslog.LOG_INFO, "    ")
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append('show chassis; show microcode; show system; show fan; show temperature; show powersupply; show powersupply total; show hardware-info')

    for switch_cmd in l_switch_cmd:
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
                notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
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

    filename = "{0}_{1}-{2}_{3}_fan_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (attachment_path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    
    ### We are looking for fan chassis_ID
    switch_cmd = "show fan"
    fan_status=0
    output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
        
    if output != None:
            output = str(output)
            fan_status = bytes(output, "utf-8").decode("unicode_escape")
            fan_status = fan_status.replace("', '","")
            fan_status = fan_status.replace("']","")
            fan_status = fan_status.replace("['","")
            print(fan_status)
    else:
            exception = "Timeout"
            notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
            send_message_detailed(notif)
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
    if "NO" in fan_status:
        try:
            chassis_id = re.findall(r"(.*?)/--         1       NO", fan_status)[0]
            print(chassis_id)
        except IndexError:
            print("Index error in regex")
            syslog.syslog(syslog.LOG_INFO, "Index error in regex on chassis_id")
            exit()
    else:
        print("FAN Chassis ID Not found we set value Unknown")
        syslog.syslog(syslog.LOG_INFO, "FAN Chassis ID Not found we set value Unknown")
        chassis_id="Unknown"

    subject = ("Preventive Maintenance Application - FAN issue issue detected on OmniSwitch: {0} / {1}").format(host,ipadd)
    if chassis_id == "Unknown":
        action = ("A Fan unit  is inoperable OmniSwitch (Hostname: {0})").format(host)
        result = "Find enclosed to this notification the log collection for further analysis. Please replace the faulty FAN as soon as possible."
    else:
        action = ("The Fan unit {0} is Down or running abnormal on OmniSwitch (Hostname: {1})").format(chassis_id, host)
        result = "Find enclosed to this notification the log collection for further analysis"
    category = "fan"
    return filename_path, subject, action, result, category

# Function to collect several command outputs related to NI module
def collect_command_output_ni(switch_user, switch_password, ni_id, host, ipadd):
    """ 
    This function takes entries arguments the  Network Interface module ID. This function is called when an issue is observed on NI module hardware
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str ni_id:                 Switch Network Interface module ID
    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_ni")
    syslog.syslog(syslog.LOG_INFO, "    ")
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show chassis; show microcode; show system; show module; show module long; show hardware-info")

    for switch_cmd in l_switch_cmd:
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
                notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
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

    filename = "{0}_{1}-{2}_{3}_ni_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (attachment_path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - NI Hardware Module issue detected on OmniSwitch: {0} / {1}").format(host,ipadd)
    action = ("The NI unit {0}  is Powered Down on OmniSwitch (Hostname: {1}). Please refer to the hardware guide, when NI module is replaced by exact same model, hotswap is supported, otherwise a reboot is required.").format(ni_id,host)
    result = "Find enclosed to this notification the log collection for further analysis."
    category = "ni"
    return filename_path, subject, action, result, category

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
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_ps")
    syslog.syslog(syslog.LOG_INFO, "    ")
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show chassis; show microcode; show system; show virtual-chassis topology; show fan; show temperature; show powersupply; show powersupply total;  show powersupply chassis-id 1 1; show powersupply chassis-id 1 2; show powersupply chassis-id 2 1; show powersupply chassis-id 2 2; show hardware-info")

    for switch_cmd in l_switch_cmd:
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
                notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
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
    ps_status = "UP"
    if "UNPLUG" in output_decode:
        syslog.syslog(syslog.LOG_INFO, "UNPLUG in output_decode")
        print("Power Supply is in UNPLUGGED state")
        ps_status = "UNPLUGGED"
    if "904072-90" in output_decode:
        if "Failure-Shutdown" in output_decode:
            syslog.syslog(syslog.LOG_INFO, "PS Part Number is 904072-90 and unit status is Failure-Shutdown")
            print("Power Supply Part number is 903747-90")
            ps_status = "UNSUPPORTED"

    if "902916-90" in output_decode:
        if "Running" in output_decode:
            syslog.syslog(syslog.LOG_INFO, "PS Part Number is 902916-90 and unit status is running")
            print("Power Supply Part number is 903747-90")
            ps_status = "SUPPORTED"

    filename = "{0}_{1}-{2}_{3}_ps_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (attachment_path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - Power Supply issue detected on OmniSwitch: {0} / {1}").format(host,ipadd)
    if ps_status == "UNPLUGGED":
        action = ("The Power Supply unit {0}  is UNPLUGGED on OmniSwitch (Hostname: {1}). Plug the Power Supply if not done and check the Fan and Power supply have the same Airflow direction (Airflow of both power supply and fan tray has to be in the same direction for the switch to cool down).").format(psid,host)
        result = "Find enclosed to this notification the log collection for further analysis."
    elif ps_status == "UNSUPPORTED":
        action = ("The Power Supply unit {0}  is DOWN on OmniSwitch (Hostname: {1}). If the Power Supply Part Number is 904072-90 you have to upgrade AOS software to 8.8R01 in order to resolve this issue.").format(psid,host)
        result = "Find enclosed to this notification the log collection for further analysis. More details in the Technical Knowledge Base https://myportal.al-enterprise.com/alebp/s/tkc-redirect?000066475."
    elif psid == "Unknown":
        action = ("A Power Supply unit  is Down or running abnormal \"Power Supply operational state changed to UNPOWERED\" on OmniSwitch (Hostname: {0})").format(host)
        result = "Find enclosed to this notification the log collection for further analysis."
    else:
        action = ("The Power Supply unit {0} is Down or running abnormal on OmniSwitch (Hostname: {1})").format(psid, host)
        result = "Find enclosed to this notification the log collection for further analysis."
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
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_vc")
    syslog.syslog(syslog.LOG_INFO, "    ")
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show virtual-chassis vf-link; show virtual-chassis auto-vf-link-port; show virtual-chassis neighbors; debug show virtual-chassis topology")

    for switch_cmd in l_switch_cmd:
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
                notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
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

    filename = "{0}_{1}-{2}_{3}_vcmm_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (attachment_path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - Virtual Chassis issue detected on OmniSwitch: {0}").format(ipadd)
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
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_linkagg")
    syslog.syslog(syslog.LOG_INFO, "    ")
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append(("show interfaces alias; show linkagg; show linkagg agg {0}; show linkagg agg {0} port").format(agg))

    for switch_cmd in l_switch_cmd:
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
                notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
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

    filename = "{0}_{1}-{2}_{3}_linkagg_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (attachment_path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - A LinkAgg Port Leave occurs on OmniSwitch: {0} / {1}").format(host, ipadd)
    action = ("A LinkAgg Port Leave has been detected in OmniSwitch(Hostname: {0}) Aggregate ID {1}").format(host, agg)
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
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_poe")
    syslog.syslog(syslog.LOG_INFO, "    ")
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show system; show interfaces alias; show lldp remote-system; show configuration snapshot lanpower; \
        show powersupply total; show lanpower slot 1/1 ; show lanpower slot 1/1 port-config; show lanpower power-rule; show lanpower chassis 1 capacitor-detection; \
        show lanpower chassis 1 usage-threshold; show lanpower chassis 1 ni-priority; show lanpower slot 1/1 high-resistance-detection; \
        show lanpower slot 1/1 priority-disconnect; show lanpower slot 1/1 class-detection")

    for switch_cmd in l_switch_cmd:
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
                notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
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

    filename = "{0}_{1}-{2}_{3}_poe_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (attachment_path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    lanpower_settings_status = 0
    switch_cmd = "show configuration snapshot lanpower"
    output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
        
    if output != None:
        output = str(output)
        output_decode = bytes(output, "utf-8").decode("unicode_escape")
        output_decode = output_decode.replace("', '","")
        output_decode = output_decode.replace("']","")
        lanpower_settings_status = output_decode.replace("['","")
        print(lanpower_settings_status)
    else:
        exception = "Timeout"
        notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message_detailed(notif)
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
    if "capacitor-detection enable" in lanpower_settings_status:
        print("Capacitor detection enabled!")
        syslog.syslog(syslog.LOG_INFO, "Capacitor detection enabled!")
        capacitor_detection_status = "enabled"
    else:
        capacitor_detection_status = "disabled"
        syslog.syslog(syslog.LOG_INFO, "Capacitor detection disabled!")
    if "high-resistance-detection enable" in lanpower_settings_status:
        print("High Resistance detection enabled!")
        syslog.syslog(syslog.LOG_INFO, "High Resistance detection enabled!")
        high_resistance_detection_status = "enabled"
    else:
        high_resistance_detection_status = "disabled"
        syslog.syslog(syslog.LOG_INFO, "High Resistance detection disabled!")
    print(reason)
    if reason == "(Illegal class)":
        subject = ("Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port {2} - reason: {3}").format(host,ipadd,port,reason)
        action = ("A PoE issue has been detected on OmniSwitch( Hostname : {0} ) syslogs with reason {1}. The OmniSwitch POE controller requires that the same class be detected on both pairs before passing detection and sending POE power to the port. When it detects different classes from the same device, power is denied until 4pair is disabled").format(host, reason)
        result = "Find enclosed to this notification the log collection for further analysis"
    elif reason == "Fail due to out-of-range capacitor value" or reason == "Port is off: Voltage injection into the port (Port fails due to voltage being applied to the port from external source)" and high_resistance_detection_status == "enabled":
        subject = ("Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port {2} - reason: {3}").format(host,ipadd,port,reason)
        action = ("A PoE issue has been detected on OmniSwitch( Hostname : {0} ) syslogs. High Resistance Detection is {1}. Please disable the high-resistance-detection (lanpower slot x/1 high-resistance-detection disable) if not necessary or disable the Lanpower on port that are non Powered Devices (lanpower port x/x/x admin-state disable)").format(host, high_resistance_detection_status)
        result = "Find enclosed to this notification the log collection for further analysis"
    elif reason == "Fail due to out-of-range capacitor value" or reason == "Port is off: Voltage injection into the port (Port fails due to voltage being applied to the port from external source)" and capacitor_detection_status == "enabled":
        subject = ("Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port {2} - reason: {3}").format(host,ipadd,port,reason)
        action = ("A PoE issue has been detected on OmniSwitch( Hostname : {0} ) syslogs. Capacitor Detection is {1}. Please disable the capacitor-detection (lanpower slot x/1 capacitor-detection disable)  if not necessary or disable the Lanpower on port that are non Powered Devices (lanpower port x/x/x admin-state disable)").format(host, capacitor_detection_status)
        result = "Find enclosed to this notification the log collection for further analysis"
    elif reason == "Port is off: Voltage injection into the port (Port fails due to voltage being applied to the port from external source)":
        subject = ("Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port {2} - reason: {3}").format(host,ipadd,port,reason)
        action = ("A PoE issue has been detected on OmniSwitch( Hostname : {0} ) syslogs. Please disable the Lanpower on port that are non Powered Devices (lanpower port x/x/x admin-state disable)").format(host)
        result = "Find enclosed to this notification the log collection for further analysis"
    elif reason == "Port is off: Over temperature at the port (Port temperature protection mechanism was activated)" or reason == "(Port temperature protection mechanism was activated)":
        subject = ("Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port {2} - reason: {3}").format(host,ipadd,port,reason)
        action = ("A PoE issue has been detected on OmniSwitch( Hostname : {0} ) syslogs. Please upgrade the switch to AOS 8.7R03 for supporting latest Lanpower APIs and monitor. If issue still persists, try a reload of Lanpower (lanpower slot x/x service stop; lanpower slot x/x service start)").format(host)
        result = "Find enclosed to this notification the log collection for further analysis"
    elif reason == "Non-standard PD connected":
        subject = ("Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port {2} - reason: {3}").format(host,ipadd,port,reason)
        action = ("A PoE issue has been detected on OmniSwitch( Hostname : {0} ) syslogs. A non-powered device is connected to PoE port, please disable the lanpower on this port if you want to remove this error message (lanpower port x/x/x admin-state disable)").format(host)
        result = "Find enclosed to this notification the log collection for further analysis"       
    elif reason == "Port is off: Overload state (Overload state according to 802.3AF/AT, current is above Icut)":
        subject = ("Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port {2} - reason: {3}").format(host,ipadd,port,reason)
        action = ("A PoE issue has been detected on OmniSwitch( Hostname : {0} ) syslogs and port is in Denied State. This issue is fixed in AOS 8.6R02. If issue still persists, try a reload of Lanpower (lanpower slot x/x service stop; lanpower slot x/x service start)").format(host)
        result = "Find enclosed to this notification the log collection for further analysis"
    elif reason == "Port is yet undefined (Getting this status means software problem)" or reason == "Internal hardware fault (Port does not respond, hardware fault, or system initialization)":
        subject = ("Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port {2} - reason: {3}").format(host,ipadd,port,reason)
        action = ("A PoE issue has been detected on OmniSwitch( Hostname : {0} ) syslogs. Please collect logs and contact ALE Customer Support").format(host)
        result = "Find enclosed to this notification the log collection for further analysis" 
    elif reason == "Port is off: Power budget exceeded (Power Management function shuts down port, due to lack of power. Port is shut down or remains off)":
        subject = ("Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port {2} - reason: {3}").format(host,ipadd,port,reason)
        action = ("A PoE issue has been detected on OmniSwitch( Hostname : {0} ) syslogs and port is in Denied State. Please verify the Active Bank is compliant with your OmniSwitch model. If Switch model is OS6860N-P48 please ensure the latest CPLD firmware is applied, more details on Technical Knowledge Base  https://myportal.al-enterprise.com/alebp/s/tkc-redirect?000066680.").format(host)
        result = "Find enclosed to this notification the log collection for further analysis"
    elif reason == "Port is off: Main supply voltage is low (Mains voltage is lower than Min Voltage limit)":
        subject = ("Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port {2} - reason: {3}").format(host,ipadd,port,reason)
        action = ("A PoE issue has been detected on OmniSwitch( Hostname : {0} ) syslogs and port is in Denied State. Please collect logs and contact ALE Customer Support. If Switch model is OS6465H-P6 or OS6465H-P12 with a power supply 75W/48V: only 802.3at Powered Devices are supported.").format(host)
        result = "Find enclosed to this notification the log collection for further analysis"                  
    else:
        subject = ("Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port {2} - reason: {3}").format(host,ipadd,port,reason)
        action = ("A PoE issue has been detected on OmniSwitch( Hostname : {0} ) syslogs. Please collect logs and contact ALE Customer Support").format(host)
        result = "Find enclosed to this notification the log collection for further analysis"         
    category = "poe"
    return filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status


# Function to collect several command outputs related to Digital Diagnostics Monitoring
def collect_command_output_ddm(switch_user, switch_password, host, ipadd, chassis, port, slot, ddm_type, threshold, sfp_power):
    """ 
    This function takes IP Address and Hostname, slot and port number
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API
    :param str port:                  Switch port without unit/slot
    :param str slot:                  Switch slot number
    :param str ddm_type:              DDM Treshold type (Supply current, Rx optical power, temperature )
    :param str threshold:             DDM Treshold level (low, high)
    :param str sfp_power:             value in mA or Dbm
    :param str ipadd:                 Switch IP address
    :param str host:                  Switch Hostname
    :return:                          filename_path,subject,action,result,category
    """
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_ddm")
    syslog.syslog(syslog.LOG_INFO, "    ")
    text = "More logs related to the Digital Diagnostics Monitoring (DDM) noticed on OmniSwitch: {0} \n\n\n".format(ipadd)
    text = "########################################################################"

    l_switch_cmd = []
    l_switch_cmd.append(("show system; show transceivers slot {0}/1; show interfaces; show interfaces status; show lldp remote-system").format(slot))

    for switch_cmd in l_switch_cmd:
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
                notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
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

    filename = "{0}_{1}-{2}_{3}_ddm_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (attachment_path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - The SFP on OmniSwitch: {0}/{1} - crossed DDM (Digital Diagnostics Monitoring) threshold").format(host,ipadd)
    action = ("The SFP {0}/{1}/{2} on OmniSwitch {3}/{4} crossed DDM (Digital Diagnostics Monitoring) threshold {5} {6}: {7}").format(chassis, slot, port, host, ipadd, threshold, ddm_type, sfp_power)
    result = "Find enclosed to this notification the log collection for further analysis. Please replace the Fiber Optical Transceiver or Fiber cable and check if issue still persists."
    category = "ddm"
    return filename_path, subject, action, result, category


# Function to collect OmniSwitch IP Service/AAA Authentication status based on protocol received as argument
def collect_command_output_aaa(switch_user, switch_password, protocol, ipadd):
    """ 
    This function takes IP Address and protocol as argument. This function is called when an authentication failure is noticed for specified protocol
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API
    :param str protocol:                  AAA Protocol (HTTPS, FTP, TELNET, SSH, NTP, SNMP, RADIUS)
    :param str ipadd:                     Switch IP address
    :return:                              filename_path,subject,action,result,category
    """
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_aaa")
    syslog.syslog(syslog.LOG_INFO, "    ")
    service_status = 0
    protocol_lower_case = 0
    if protocol == "HTTPS":
        protocol_lower_case = "http"
        switch_cmd = "show ip service | grep {0}".format(protocol_lower_case)
    elif protocol == "Console":
        protocol = "0"
        switch_cmd = "show ip service | grep {0}".format(protocol)
        protocol = "console"
    else:
        switch_cmd = "show ip service | grep {0}".format(protocol)
    
    output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
        
    if output != None:
        output = str(output)
        service_status=0
        output_decode = bytes(output, "utf-8").decode("unicode_escape")
        output_decode = output_decode.replace("', '","")
        output_decode = output_decode.replace("']","")
        service_status = output_decode.replace("['","")
        service_status = str(service_status)
    else:
        exception = "Timeout"
        notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message_detailed(notif)
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
    if "enabled" in service_status or service_status != 0:
        print("Protocol " + protocol + " enabled!")
        syslog.syslog(syslog.LOG_INFO, "Protocol " + protocol + " enabled!")
        service_status = "enabled"
    else:
        service_status = "disabled"
        syslog.syslog(syslog.LOG_INFO, "Protocol " + protocol + " disabled!")


    switch_cmd = "show configuration snapshot aaa | grep \"aaa authentication {0}\"".format(protocol)
    aaa_status=0
    try:
        output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
        
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
                syslog.syslog(syslog.LOG_INFO, "Protocol aaa authentication enabled")
            else:
                aaa_status = "disabled"
                syslog.syslog(syslog.LOG_INFO, "Protocol aaa authentication disabled")
        except:
            aaa_status = "disabled"
            syslog.syslog(syslog.LOG_INFO, "No Protocol aaa authentication - status disabled")
            pass

    except (AttributeError,FileNotFoundError) as exception:
        notif = ("Command {0} execution on OmniSwitch {1} failed - {2}").format(switch_cmd,ipadd, exception)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message_detailed(notif)
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
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function authentication_failure")
    syslog.syslog(syslog.LOG_INFO, "    ")
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show ip service; show aaa authentication")

    for switch_cmd in l_switch_cmd:
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
                notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
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

    filename = "{0}_{1}-{2}_{3}_authentication_logs".format(date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (attachment_path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = ("Preventive Maintenance Application - Authentication failure noticed on OmniSwitch: {0}").format(ipadd)
    action = ("An Authentication failure has been detected on OmniSwitch ( Hostname: {0} ) from User: {1} - source IP Address: {2} - protocol: {3}").format(host, user, source_ip, protocol)
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
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_lldp_port_description")
    syslog.syslog(syslog.LOG_INFO, "    ")
    lldp_port_description = lldp_mac_address = 0
    lldp_port = ""
    switch_cmd = "show lldp port {0} remote-system".format(port)
    try:
        output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
        
        if output != None:
            output = str(output)
            output_decode = bytes(output, "utf-8").decode("unicode_escape")
            output_decode = output_decode.replace("', '","")
            output_decode = output_decode.replace("']","")
            lldp_port = output_decode.replace("['","")
        else:
            exception = "Timeout"
            notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
            send_message_detailed(notif)
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
    except (AttributeError, FileNotFoundError) as exception:
        notif = ("Command {0} execution on OmniSwitch {1} failed - {2}").format(switch_cmd,ipadd, exception)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message_detailed(notif)
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
    if "Port Description" in lldp_port:
        try: 
           print(lldp_port)
           lldp_port_description = re.findall(r"Port Description            = (.*?),", lldp_port)[0]
           lldp_mac_address = re.findall(r"Port (.*?):\n", lldp_port)[1]
        except IndexError:
            print("Index error in regex")
            syslog.syslog(syslog.LOG_INFO, "Index error in regex for lldp_mac_address or lldp_port_capability")
            pass           
        except exception as exception:
            print(exception)
            syslog.syslog(syslog.LOG_INFO, "LLDP Port Description output failed - " + exception)
            lldp_port_description = lldp_mac_address = 0
            pass
    return lldp_port_description, lldp_mac_address



def collect_command_output_lldp_port_capability(switch_user, switch_password, port, ipadd):
    """ 
    This function takes IP Address and port as argument. This function is called when we want additionnal information on equipment connected to Switch Interface
    This function returns LLDP Port Capability field value
    :param str port:                      Switch Interface Port
    :param str ipadd:                     Switch IP address
    :return:                              lldp_capability
    """
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function collect_command_output_lldp_port_capability")
    syslog.syslog(syslog.LOG_INFO, "    ")
    lldp_port_capability = lldp_mac_address = lldp_port = 0
    switch_cmd = "show lldp port {0} remote-system".format(port)
    try:
        syslog.syslog(syslog.LOG_INFO, "SSH Session start")
        syslog.syslog(syslog.LOG_INFO, "Command executed: " + switch_cmd)         
        output, exception = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
        syslog.syslog(syslog.LOG_INFO, "Exception: " + exception)
        if output != None:
            output = str(output)
            output_decode = bytes(output, "utf-8").decode("unicode_escape")
            output_decode = output_decode.replace("', '","")
            output_decode = output_decode.replace("']","")
            lldp_port = output_decode.replace("['","")
        else:
            exception = "Timeout"
            notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
            send_message_detailed(notif)
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
    except (AttributeError,FileNotFoundError) as exception:
        notif = ("Command {0} execution on OmniSwitch {1} failed - {2}").format(switch_cmd,ipadd, exception)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message_detailed(notif)
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
    if "Port Description" in lldp_port:
        syslog.syslog(syslog.LOG_INFO, "Port description in lldp_port")
        try: 
           lldp_port_capability = re.findall(r"Capabilities Supported      = (.*?),", lldp_port)[0]
           lldp_mac_address = re.findall(r"Port (.*?):\n", lldp_port)[1]
           syslog.syslog(syslog.LOG_INFO, "lldp_port_capability: " + lldp_port_capability)
        except IndexError:
            print("Index error in regex")
            syslog.syslog(syslog.LOG_INFO, "Index error in regex for lldp_mac_address or lldp_port_capability")
            pass
        except UnboundLocalError as error:
            print(str(error))
            syslog.syslog(syslog.LOG_INFO, "Exception: " + error)
            lldp_port_capability = 0
            pass           
        except exception as error:
            print(str(error))
            syslog.syslog(syslog.LOG_INFO, "Exception: " + error)
            lldp_port_capability = 0
            pass
    return lldp_port_capability, lldp_mac_address


# Function to collect OmniSwitch LLDP Remote System Port Description
def get_arp_entry(switch_user, switch_password, lldp_mac_address, ipadd):
    """ 
    This function takes Switch IP Address and Device MAC Address. This function is called when we want to find the Device IP Address from ARP Table
    This function returns LLDP Port Description field value
    :param str lldp_mac_address:          Device MAC Address found from LLDP Port Description
    :param str ipadd:                     Switch IP address
    :return:                              device_ip
    """
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function get_arp_entry")
    syslog.syslog(syslog.LOG_INFO, "    ")
    device_ip = 0

    switch_cmd = "show arp | grep \"{0}\"".format(lldp_mac_address)
    try:
        output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
        
        if output != None:
            output = str(output)
            output_decode = bytes(output, "utf-8").decode("unicode_escape")
            output_decode = output_decode.replace("', '","")
            output_decode = output_decode.replace("']","")
            device_ip = output_decode.replace("['","")
        else:
            exception = "Timeout"
            notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
            send_message_detailed(notif)
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
    except (AttributeError,FileNotFoundError) as exception:
        notif = ("Command {0} execution on OmniSwitch {1} failed - {2}").format(switch_cmd,ipadd, exception)
        syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
        syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
        send_message_detailed(notif)
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
    try:
        if "{0}".format(lldp_mac_address) in device_ip:
            print(device_ip)
            try:
                device_ip = re.findall(r" ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}) ", device_ip)[0]
                syslog.syslog(syslog.LOG_INFO, "Device IP Address found in ARP Table: " + device_ip)
            except IndexError:
                print("Index error in regex")
                syslog.syslog(syslog.LOG_INFO, "Index error in regex for device_ip")
        else:
            print("No ARP Entry for this MAC Address")
            syslog.syslog(syslog.LOG_INFO, "No ARP Entry for this MAC Address")
    except:
        pass
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
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function check_save")
    syslog.syslog(syslog.LOG_INFO, "    ")
    if not os.path.exists(dir + '/decisions_save.conf'):
        try:
            syslog.syslog(syslog.LOG_INFO, "File does not exist - file is created")
            open(dir + '/decisions_save.conf', 'w', errors='ignore').close()
            return "0"
        except OSError as exception:
            print(exception)
            syslog.syslog(syslog.LOG_INFO, "Permission error when creating file" + dir + "/decisions_save.conf: " + exception)
            os._exit(1)
    content = open(dir + "/decisions_save.conf", "r", errors='ignore')
    file_lines = content.readlines()
    content.close()

    for line in file_lines:
        print(line)
        if "{0},{1},{2},always".format(ipadd, port, type) in line:
            syslog.syslog(syslog.LOG_INFO, "Decision saved is always we return 1")
            return "1"
        if "{0},{1},{2},never".format(ipadd, port, type) in line:
            syslog.syslog(syslog.LOG_INFO, "Decision saved is never we return -1")
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
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function add_new_save")
    syslog.syslog(syslog.LOG_INFO, "    ")
    if not os.path.exists(dir + '/decisions_save.conf'):
        try:
            syslog.syslog(syslog.LOG_INFO, "File does not exist - file is created")
            open(dir + '/decisions_save.conf', 'w').close()
            subprocess.call(['chmod', '0755', dir + '/decisions_save.conf'])
        except OSError as exception:
            print(exception)
            syslog.syslog(syslog.LOG_INFO, "Permission error when creating file" + dir + "/decisions_save.conf: " + exception)
            os._exit(1)

    fileR = open(dir + "/decisions_save.conf", "r", errors='ignore')
    text = fileR.read()
    fileR.close()

    textInsert = "{0},{1},{2},{3}\n".format(ipadd, port, type, choice)
    try:
        fileW = open(dir + "/decisions_save.conf", "w", errors='ignore')
        fileW.write(textInsert + text)
        syslog.syslog(syslog.LOG_INFO, "Data inserted: " + textInsert + text)
        fileW.close()
    except OSError as exception:
        print(exception)
        syslog.syslog(syslog.LOG_INFO, "Permission error when creating file" + dir + "/decisions_save.conf: " + exception)
        os._exit(1)

def script_has_run_recently(seconds,ip,function):
    """ 
    This function is called on scenario when we prevent to run the script again and again because we receive remanent logs or further logs after 1st notification was sent
    :param str seconds:              Runtime
    :param str ip:                   Switch IP Address
    :param str function:             Which use case: loop, flapping
    :return:                         True (if runtime less than 5 minutes) or False
    """
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function script_has_run_recently")
    syslog.syslog(syslog.LOG_INFO, "    ")
    filename = (dir + '/last-runtime_{0}.txt').format(function)
    current_time = int(time.time())
    text = "{0},{1},{2}\n".format(str(current_time),ip, function)
    try:
        content = open(dir + "/last-runtime_{0}.txt".format(function), "r", errors='ignore')
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
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function check_timestamp_and_function")
    syslog.syslog(syslog.LOG_INFO, "    ")
    content = open(dir + "/last-runtime_{0}.txt".format(function), "r", errors='ignore')
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
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function detect_port_loop")
    syslog.syslog(syslog.LOG_INFO, "    ")
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
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function check_timestamp")
    syslog.syslog(syslog.LOG_INFO, "    ")
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
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function isEssential")
    syslog.syslog(syslog.LOG_INFO, "    ")
    ips_address = list()
    with open(dir + "/Essential_ip.csv") as csv_file:
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
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function isUpLink")
    syslog.syslog(syslog.LOG_INFO, "    ")
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
            else:
                exception = "Timeout"
                notif = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
                syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
                send_message_detailed(notif)
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
        except (AttributeError,FileNotFoundError) as exception:
            notif = ("Command {0} execution on OmniSwitch {1} failed - {2}").format(switch_cmd,ipadd, exception)
            syslog.syslog(syslog.LOG_INFO, "Notification: " + notif)
            syslog.syslog(syslog.LOG_INFO, "Logs collected - Calling VNA API - Rainbow notification")
            send_message_detailed(notif)
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
        
def disable_port(switch_user, switch_password, ipadd, portnumber):
    """ 
    This function disables the port where there is a loop  on the switch put in arguments.

    :param str user:                Switch user login
    :param str password:            Switch user password
    :param str ipadd:               Switch IP Address
    :param str portnumber:          The Switch port where there is a loop. shape : x/y/z with x = chassis n ; y = slot n ; z = port n
    :return:                        None
    """
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function disable_port")
    syslog.syslog(syslog.LOG_INFO, "    ")
    cmd = "interfaces port {0} admin-state disable".format(portnumber)
    # ssh session to start python script remotely
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)

def port_monitoring(switch_user, switch_password, port, ipadd):
    """ 
    This function executes a port monitoring (packet capture) on port received in argument  
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str port:                  Switch Interface/Port ID <chasis>/<slot>/>port>
    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
    syslog.syslog(syslog.LOG_INFO, "    ")
    syslog.syslog(syslog.LOG_INFO, "Executing function port_monitoring")
    syslog.syslog(syslog.LOG_INFO, "    ")
   ## Execute port monitoring on port with subprocess.call as we are not expecting output
    switch_cmd = ("no port-monitoring 1; no port-mirroring 1")
    cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user, ipadd, switch_cmd)
    try:
        output = subprocess.call(cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
        return True
    except subprocess.SubprocessError:
        print("Issue when executing command")
        syslog.syslog(syslog.LOG_INFO, "Issue when executing command port_monitoring " + output) 
    except Exception as exception:
        print("Issue when executing command")
        syslog.syslog(syslog.LOG_INFO, "Issue when executing command port_monitoring " + output) 

    switch_cmd = ("port-monitoring 1 source port " + port + " file /flash/pmonitor.enc size 1 timeout 30 inport capture-type full enable")
    cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(switch_password, switch_user, ipadd, switch_cmd)
    try:
        output = subprocess.call(cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
        return True
    except subprocess.SubprocessError:
        print("Issue when executing command")
        syslog.syslog(syslog.LOG_INFO, "Issue when executing command port_monitoring " + output) 
    except Exception as exception:
        print("Issue when executing command")
        syslog.syslog(syslog.LOG_INFO, "Issue when executing command port_monitoring " + output)        

if __name__ == "__main__":
#    a = isUpLink("admin", "switch", "1/1/21", "10.130.7.239")
#    print(a)
#    b = isEssential("10.130.7.14")
#    print(b)
    try:
        syslog.syslog(syslog.LOG_INFO, "Starting tests") 
        switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()
        jid = "570e12872d768e9b52a8b975@openrainbow.com"
        switch_password = "switch"
        switch_user = "admin"
        ipadd = "192.168.80.82"
        cmd = "show system"
        host = "LAN-6860N-2"
        port = "1/1/58"
        source = "Unknown Unicast"
        decision = 0
        #ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)
        filename_pmd = "/flash/pmd/pmd-agCmm-04.23.2021-14.34.58"
        date = datetime.date.today()
        localFilePath = filename_pmd.replace("/", "_")
        localFilePath = ("/tftpboot/{0}_{1}_{2}").format(date, ipadd, localFilePath)
        #get_file_sftp(switch_user, switch_password, ipadd, filename_pmd, localFilePath)
        #filename_path, subject, action, result, category = get_tech_support_sftp(switch_user, switch_password, host, ipadd)
        filename_path = "/var/log/server/support_tools_OmniSwitch.log"
        #send_file_detailed(filename_path, subject, action, result, category)
        #filename_path, subject, action, result, category = collect_command_output_network_loop(switch_user, switch_password, ipadd, port)
        #send_file(filename_path, subject, action, result,category, jid)
        #filename_path, subject, action, result, category = collect_command_output_storm(switch_user, switch_password, port, source, decision, host, ipadd)
        #send_file(filename_path, subject, action, result,category, jid)
        reason="Fail due to out-of-range capacitor value"
        port="34"
        #filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status = collect_command_output_poe(switch_user, switch_password, host, ipadd, port, reason)
        #send_file(filename_path, subject, action, result,category, jid)
        agg = "6"
        #filename_path, subject, action, result, category = collect_command_output_linkagg(switch_user, switch_password, agg, host, ipadd)
        #send_file(filename_path, subject, action, result,category, jid)
        vcid = "2"
        #filename_path, subject, action, result, category = collect_command_output_vc(switch_user, switch_password, vcid, host, ipadd)
        #send_file(filename_path, subject, action, result,category, jid)
        psid = "2"
        #filename_path, subject, action, result, category = collect_command_output_ps(switch_user, switch_password, psid, host, ipadd)
        #send_file(filename_path, subject, action, result,category, jid)
        source = "Access Guardian"
        port="1/1/59"
        decision = "0"
        #filename_path, subject, action, result, category = collect_command_output_violation(switch_user, switch_password, port, source, decision, host, ipadd)
        #send_file(filename_path, subject, action, result,category, jid)
        protocol = "Console"
        user = "toto"
        source_ip = "10.130.7.17"
        #service_status, aaa_status = collect_command_output_aaa(switch_user, switch_password, protocol, ipadd)
        #filename_path, subject, action, result, category = authentication_failure(switch_user, switch_password, user, source_ip, protocol, service_status, aaa_status, host, ipadd)
        #send_file(filename_path, subject, action, result,category, jid)

        #status_changes, link_quality = collect_command_output_flapping(switch_user, switch_password, port, ipadd)
        #filename_path, subject, action, result, category = collect_command_output_health_cpu(switch_user, switch_password, host, ipadd)
        #send_file(filename_path, subject, action, result,category, jid)
        #filename_path, subject, action, result, category = collect_command_output_health_memory(switch_user, switch_password, host, ipadd)
        #send_file(filename_path, subject, action, result,category, jid)
        type = "receive"
        filename_path, subject, action, result, category = collect_command_output_health_port(switch_user, switch_password, port, type, host, ipadd)
        #send_file(filename_path, subject, action, result,category, jid)
        #filename_path, subject, action, result, category = collect_command_output_violation(switch_user, switch_password, port, source, decision, host, ipadd)
        #send_file(filename_path, subject, action, result,category, jid)
        adjacency_id = "1223456366"
        #filename_path, subject, action, result, category = collect_command_output_spb(switch_user, switch_password, host, ipadd, adjacency_id, port)
        #send_file(filename_path, subject, action, result,category, jid)
        vlan = "68-70"
        #filename_path, subject, action, result, category = collect_command_output_stp(switch_user, switch_password, decision, host, ipadd, vlan)
        #send_file(filename_path, subject, action, result,category, jid)
        fan_id = "2"
        filename_path, subject, action, result, category = collect_command_output_fan(switch_user, switch_password, fan_id, host, ipadd)
        #send_file(filename_path, subject, action, result,category, jid)
        ni_id = "3"
        filename_path, subject, action, result, category = collect_command_output_ni(switch_user, switch_password, ni_id, host, ipadd)
        #send_file(filename_path, subject, action, result,category, jid)
        filename_path, subject, action, result, category = collect_command_output_ps(switch_user, switch_password, psid, host, ipadd)
        #send_file(filename_path, subject, action, result,category, jid)
        filename_path, subject, action, result, category = collect_command_output_vc(switch_user, switch_password, vcid, host, ipadd)
        #send_file(filename_path, subject, action, result,category, jid)
        filename_path, subject, action, result, category = collect_command_output_linkagg(switch_user, switch_password, agg, host, ipadd)
        #send_file(filename_path, subject, action, result,category, jid)
        filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status = collect_command_output_poe(switch_user, switch_password, host, ipadd, port, reason)
        #send_file(filename_path, subject, action, result,category, jid)
        slot= 1 
        ddm_type = "Power"
        threshold = "low" 
        sfp_power = "0.3mA"
        #filename_path, subject, action, result, category = collect_command_output_ddm(switch_user, switch_password, host, ipadd, port, slot, ddm_type, threshold, sfp_power)
        #send_file(filename_path, subject, action, result,category, jid)
        #service_status, aaa_status = collect_command_output_aaa(switch_user, switch_password, protocol, ipadd)
        #filename_path, subject, action, result, category = authentication_failure(switch_user, switch_password, user, source_ip, protocol, service_status, aaa_status, host, ipadd)
        lldp_port_description, lldp_mac_address = collect_command_output_lldp_port_description(switch_user, switch_password, port, ipadd)
        lldp_port_capability = collect_command_output_lldp_port_capability(switch_user, switch_password, port, ipadd)
        device_ip = get_arp_entry(switch_user, switch_password, lldp_mac_address, ipadd)
        type = "ddos"
        check_save(ipadd, port, type)
        add_new_save(ipadd, port, type, choice="never")
        isEssential(ipadd)
        isUpLink(switch_user, switch_password, port, ipadd)
        port_monitoring(switch_user, switch_password, port, ipadd)
    except (RuntimeError, TypeError, NameError):
        raise
    except OSError:
        raise
    except KeyboardInterrupt:
        syslog.syslog(syslog.LOG_INFO, "KeyboardInterrupt")
        raise
    finally:
        print("End of tests")
        syslog.syslog(syslog.LOG_INFO, "End of tests")

else:
    print("Support_Tools_OmniSwitch Script called by another script")
