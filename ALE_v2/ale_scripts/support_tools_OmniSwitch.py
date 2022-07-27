#!/usr/bin/env python3

from asyncio.subprocess import PIPE
from copy import error
import sys
import os
import logging
import datetime
from time import sleep
from support_send_notification import *
import subprocess
import re
import pysftp
import paramiko
import threading
import csv
import json
# from database_conf import *
import time

from pattern import mysql_save
from time import localtime, strftime

# This script contains all functions interacting with OmniSwitches

# Function for extracting environment information from ALE_script.conf file

path = os.path.dirname(__file__)


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
    from mysql.connector import connect
    from cryptography.fernet import Fernet
    db_key=b'gP6lwSDvUdI04A8fC4Ib8PXEb-M9aTUbeZTBM6XAhpI='
    dbsecret_password=b'gAAAAABivYWTJ-2OZQW4Ed2SGRNGayWRUIQZxLckzahNUoYSJBxsg5YZSYlMdiegdF1RCAvG4FqjMXD-nNeX0i6eD7bdFV8BEw=='
    fernet = Fernet(db_key)
    db_password = fernet.decrypt(dbsecret_password).decode()
    database = connect(
		host='localhost',
		user='aletest',
		password=db_password,
		database='aledb'
		)
    db = database.cursor()
    query = "SELECT * FROM ALEUser_settings_value"
    db.execute(query)
    result = json.loads(db.fetchall()[1][2])
    return result.values()

switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass, random_id, company, room_id = get_credentials()

# Function SSH for checking connectivity before collecting logs


def ssh_connectivity_check(switch_user, switch_password, ipadd, cmd):
    """ 
    This function takes entry the command to push remotely on OmniSwitch by SSH with Python Paramiko module
    Paramiko exceptions are handled for notifying Network Administrator if the SSH Session does not establish

    :param str ipadd                  Command pushed by SSH on OmnISwitch
    :param str cmd                    Switch IP address
    :return:  stdout, stderr          If exceptions is returned on stderr a notification is sent to Network Administrator, else we log the session was established
    """
    print(cmd)
    runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

    try:
        p = paramiko.SSHClient()
        p.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        p.connect(ipadd, port=22, username=switch_user,
                  password=switch_password, timeout=60.0, banner_timeout=200)
    except paramiko.ssh_exception.SSHException:
        exception = "Timeout"
        print("Timeout when establishing SSH Session")
        info = (
            "Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
        _info = info + ' ; ' + 'command executed - {0}'.format(cmd)
        os.system('logger -t montag -p user.info ' + info)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,
                       result='failure', reason=_info, exception=exception)
        except UnboundLocalError as error:
            print(error)
        sys.exit()
    except paramiko.ssh_exception.AuthenticationException:
        exception = "AuthenticationException"
        print("Authentication failed enter valid user name and password")
        info = (
            "SSH Authentication failed when connecting to OmniSwitch {0}, we cannot collect logs").format(ipadd)
        _info = info + ' ; ' + 'command executed - {0}'.format(cmd)
        os.system('logger -t montag -p user.info ' + info)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,
                       result='failure', reason=_info, exception=exception)
        except UnboundLocalError as error:
            print(error)
        sys.exit(0)
    except paramiko.ssh_exception.NoValidConnectionsError:
        exception = "NoValidConnectionsError"
        print("Device unreachable")
        logging.info(' SSH session does not establish on OmniSwitch ' + ipadd)
        info = ("OmniSwitch {0} is unreachable, we cannot collect logs").format(
            ipadd)
        print(info)
        _info = info + ' ; ' + 'command executed - {0}'.format(cmd)
        os.system('logger -t montag -p user.info ' + info)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,
                       result='failure', reason=_info, exception=exception)
        except UnboundLocalError as error:
            print(error)
        sys.exit(0)
    try:
        stdin, stdout, stderr = p.exec_command(cmd, timeout=120)
        #stdin, stdout, stderr = threading.Thread(target=p.exec_command,args=(cmd,))
        # stdout.start()
        # stdout.join(1200)
    except Exception:
        exception = "SSH Timeout"
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        _info = info + ' ; ' + 'command executed - {0}'.format(cmd)
        os.system('logger -t montag -p user.info ' + info)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,
                       result='failure', reason=_info, exception=exception)
        except UnboundLocalError as error:
            print(error)
        sys.exit()
    except paramiko.ssh_exception.SSHException:
        exception = "Timeout"
        print("Timeout when establishing SSH Session")
        info = (
            "Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
        _info = info + ' ; ' + 'command executed - {0}'.format(cmd)
        os.system('logger -t montag -p user.info ' + info)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,
                       result='failure', reason=_info, exception=exception)
        except UnboundLocalError as error:
            print(error)
        sys.exit()
    exception = stderr.readlines()
    exception = str(exception)
    connection_status = stdout.channel.recv_exit_status()
    print(connection_status)
    print(exception)
    if connection_status != 0:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        # send_message_detailed(info, jid1, jid2, jid3)
        _info = info + ' ; ' + 'command executed - {0}'.format(cmd)
        send_message_detailed(info, jid1, jid2, jid3)
        os.system('logger -t montag -p user.info ' + info)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,
                       result='failure', reason=info, exception=exception)
        except UnboundLocalError as error:
            print(error)
        sys.exit(2)
    else:
        info = ("SSH Session established successfully on OmniSwitch {0}").format(
            ipadd)
        _info = info + ' ; ' + 'command executed - {0}'.format(cmd)
        os.system('logger -t montag -p user.info ' + info)

        output = stdout.readlines()
        # We close SSH Session once retrieved command output
        p.close()
        return output

def detect_port_loop():
    """ 
    This function detectes if there is a loop in the network ( more than 10 log in 2 seconds)

    :param:                         None
    :return int :                  If the int is equal to 1 we have detected a loop, if not the int equals 0
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


def get_file_sftp(switch_user, switch_password, ipadd, filename):
    print(filename)
    print(ipadd)
    runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
    date = datetime.date.today()
    remote_path = '/tftpboot/{0}_{1}_{2}'.format(date, ipadd, filename)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ipadd, username=switch_user,
                    password=switch_password, timeout=10.0)
        sftp = ssh.open_sftp()
        # In case of SFTP Get timeout thread is closed and going into Exception
        try:
            th = threading.Thread(target=sftp.get, args=(
                './{0}'.format(filename), remote_path))
            th.start()
            th.join(60)
        except paramiko.ssh_exception.FileNotFoundError as error:
            print(error)
            exception = "File error or wrong path"
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3,
                                  'Get File SFTP', 'Status: Failure', company)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sftp.close()
            sys.exit()
        except paramiko.ssh_exception.IOError:
            exception = "File error or wrong path"
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3,
                                  'Get File SFTP', 'Status: Failure', company)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sftp.close()
            sys.exit()
        except paramiko.ssh_exception.Exception as error:
            print(error)
            exception = "SFTP Get Timeout"
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3,
                                  'Get File SFTP', 'Status: Failure', company)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sftp.close()
            sys.exit()
        except paramiko.ssh_exception.SSHException as error:
            print(error)
            exception = error.readlines()
            exception = str(exception)
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3,
                                  'Get File SFTP', 'Status: Failure', company)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sftp.close()
            sys.exit()
    except paramiko.ssh_exception.AuthenticationException:
        exception = "SFTP Get Timeout"
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3,
                              'Get File SFTP', 'Status: Failure', company)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,
                       result='failure', reason=info, exception=exception)
        except UnboundLocalError as error:
            print(error)
        ssh.close()
        sys.exit()
    ssh.close()

    info = ("The python script execution on OmniSwitch {0}").format(ipadd)
    mysql_save(runtime=runtime, ip_address=ipadd,
               result='success', reason=info, exception='')
    return remote_path


def get_pmd_file_sftp(switch_user, switch_password, ipadd, filename):
    print(filename)
    print(ipadd)
    runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
    date = datetime.date.today()
    pmd_file = filename.replace("/", "_")
    remote_path = '/tftpboot/{0}_{1}_{2}'.format(date, ipadd, filename)
    try:
        with pysftp.Connection(host=ipadd, username=switch_user, password=switch_password) as sftp:
            # get a remote file
            sftp.get('{0}'.format(filename),
                     '/tftpboot/{0}_{1}_{2}'.format(date, ipadd, pmd_file))
    except FileNotFoundError as exception:
        print(exception)
        info = ("The download of PMD file {0} on OmniSwitch {1} failed - {2}").format(
            filename, ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3,
                              'Get PMD File SFTP', 'Status: Failure', company)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,
                       result='failure', reason=info, exception=exception)
        except UnboundLocalError as error:
            print(error)
        sftp.close()
        sys.exit()
    sftp.close()
    info = ("The download of PMD file {0} on OmniSwitch {1}").format(
        filename, ipadd)
    mysql_save(runtime=runtime, ip_address=ipadd,
               result='success', reason=info, exception='')
    return remote_path


def format_mac(mac):
    # remove delimiters and convert to lower case
    mac = re.sub('[.:-]', '', mac).lower()
    mac = ''.join(mac.split())  # remove whitespaces
    assert len(mac) == 12  # length should be now exactly 12 (eg. 008041aefd7e)
    assert mac.isalnum()  # should only contain letters and numbers
    # convert mac in canonical form (eg. 00:80:41:ae:fd:7e)
    mac = ":".join(["%s" % (mac[i:i+2]) for i in range(0, 12, 2)])
    return mac


def file_setup_qos(addr):
    content_variable = open(path + '/configqos', 'w')
    if re.search(r"\:", addr):  # mac
        setup_config = "policy condition scanner_{0} source mac {0}\npolicy action block_mac disposition deny\npolicy rule scanner_{0} condition scanner_{0} action block_mac\nqos apply\nqos enable\n".format(
            addr)
    else:
        setup_config = "policy condition scanner_{0} source ip {0}\npolicy action block_ip disposition deny\npolicy rule scanner_{0} condition scanner_{0} action block_ip\nqos apply".format(
            addr)
    content_variable.write(setup_config)
    content_variable.close()

# Function debug


def debugging(switch_user, switch_password, ipadd, appid, subapp, level):
    """ 
    This function takes entries arguments the appid, subapp and level to apply on switch for enabling or disabling debug logs

    :param str appid_1:               swlog appid function (ipv4,bcmd)
    :param str subapp_1:              swlog subapp component (all)
    :param str level_1:               swlog debug level (debug1,debug2,debug3,info)
    :script executed ssh_device:      with cmd in argument
    :return:                          None
    """

    cmd = ("swlog appid {0} subapp {1} level {2}").format(appid, subapp, level)
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)

def get_tech_support_sftp(switch_user, switch_password, host, ipadd):
    """ 
    This function takes entries arguments the OmniSwitch IP Address
    This function returns file path containing the tech_support_complete file and the notification subject, body used when calling VNA API

    :param str host:                        Switch Hostname
    :param str ipadd:                       Switch IP address
    :return:                                filename_path,subject,action,result,category
    """

    runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
    date = datetime.date.today()
    date_hm = datetime.datetime.today()
    filename = 'tech_support_complete.tar'
    try:
        p = paramiko.SSHClient()
        p.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        p.connect(ipadd, port=22, username="admin", password="switch")
    except paramiko.ssh_exception.SSHException:
        exception = "Timeout"
        print("Timeout when establishing SSH Session on OmniSwitch " + ipadd)
        info = (
            "Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
        os.system('logger -t montag -p user.info ' + info)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,
                       result='failure', reason=info, exception=exception)
        except UnboundLocalError as error:
            print(error)
        sys.exit()
    except paramiko.ssh_exception.AuthenticationException:
        print("Authentication failed enter valid user name and password on OmniSwitch " + ipadd)
        info = (
            "SSH Authentication failed when connecting to OmniSwitch {0}, we cannot collect logs").format(ipadd)
        os.system('logger -t montag -p user.info ' + info)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3,
                              'Get PMD File SFTP', 'Status: Failure', company)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd, result='failure',
                       reason=info, exception='Authentication Failure')
        except UnboundLocalError as error:
            print(error)
        sys.exit(0)
    except paramiko.ssh_exception.NoValidConnectionsError:
        print("Device unreachable")
        logging.info(' SSH session does not establish on OmniSwitch ' + ipadd)
        info = ("OmniSwitch {0} is unreachable, we cannot collect logs").format(
            ipadd)
        os.system('logger -t montag -p user.info ' + info)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3,
                              'Get PMD File SFTP', 'Status: Failure', company)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd, result='failure',
                       reason=info, exception='Device Unreachable')
        except UnboundLocalError as error:
            print(error)
        sys.exit(0)
    cmd = ("rm -rf {0}").format(filename)
    stdin, stdout, stderr = p.exec_command(cmd)
    exception = stderr.readlines()
    exception = str(exception)
    connection_status = stdout.channel.recv_exit_status()
    if connection_status != 0:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3,
                              'Get PMD File SFTP', 'Status: Failure', company)
        os.system('logger -t montag -p user.info ' + info)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,
                       result='failure', reason=info, exception=exception)
        except UnboundLocalError as error:
            print(error)
        sys.exit(2)

    stdin, stdout, stderr = p.exec_command("show tech-support eng complete")
    exception = stderr.readlines()
    exception = str(exception)
    connection_status = stdout.channel.recv_exit_status()
    if connection_status != 0:
        info = (
            "\"The show tech support eng complete\" command on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3,
                              'Get PMD File SFTP', 'Status: Failure', company)
        os.system('logger -t montag -p user.info ' + info)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,
                       result='failure', reason=info, exception=exception)
        except UnboundLocalError as error:
            print(error)
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

    f_filename = "tech_support_complete.tar"
    #### SFTP GET tech support #####
    filename_path = get_file_sftp(
        switch_user, switch_password, ipadd, f_filename)

    subject = (
        "Preventive Maintenance Application - Show Tech-Support Complete command executed on switch: {0}").format(ipadd)
    action = (
        "The Show Tech-Support Complete file {0} is collected from OmniSwitch (Hostname: {1})").format(filename_path, host)
    result = "Find enclosed to this notification the tech_support_complete.tar file"
    category = "tech_support_complete"
    mysql_save(runtime=runtime, ip_address=ipadd,
               result='success', reason=action, exception='')
    return filename_path, subject, action, result, category

# Function to collect several command outputs related to TCAM failure


def collect_command_output_tcam(switch_user, switch_password, host, ipadd):
    """ 
    This function takes entries arguments the OmniSwitch IP Address where TCAM (QOS) failure is noticed.
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
    runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show qos config")
    l_switch_cmd.append("show qos statistics")
    l_switch_cmd.append("show qos log")
    l_switch_cmd.append("show qos rules")
    l_switch_cmd.append("show tcam utilization detail")

    for switch_cmd in l_switch_cmd:
        cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
            switch_password, switch_user, ipadd, switch_cmd)
        try:
            output = ssh_connectivity_check(
                switch_user, switch_password, ipadd, switch_cmd)
            output = subprocess.check_output(
                cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
            if output != None:
                output = output.decode('UTF-8').strip()
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output)
            else:
                exception = "Timeout"
                info = (
                    "Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                _info = info + ' ; ' + \
                    'command executed - {0}'.format(switch_cmd)
                os.system('logger -t montag -p user.info ' + info)
                # send_message_detailed(info, jid1, jid2, jid3)
                send_message_detailed(info, jid1, jid2, jid3)
                try:
                    mysql_save(runtime=runtime, ip_address=ipadd,
                               result='failure', reason=_info, exception=exception)
                except UnboundLocalError as error:
                    print(error)
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=_info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
        except subprocess.FileNotFoundError as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=_info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_tcam_logs".format(
        date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = (
        "Preventive Maintenance Application - A TCAM failure (QOS) is noticed on switch: {0}").format(ipadd)
    action = (
        "A TCAM failure (QOS) is noticed on OmniSwitch (Hostname: {0})").format(host)
    result = "Find enclosed to this notification the log collection of command outputs"
    category = "qos"
    mysql_save(runtime=runtime, ip_address=ipadd,
               result='success', reason=action, exception='')
    return filename_path, subject, action, result, category


def collect_command_output_network_loop(switch_user, switch_password, ipadd, port):
    """ 
    This function takes entries arguments the OmniSwitch IP Address where Network Loop is noticed.
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str port:                  Switch Interface port where loop is noticed
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
    runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show system")
    l_switch_cmd.append("show chassis")
    l_switch_cmd.append("show interfaces " + port + " status")
    l_switch_cmd.append("show mac-learning  port " + port)
    l_switch_cmd.append("show vlan members port " + port)

    for switch_cmd in l_switch_cmd:
        cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
            switch_password, switch_user, ipadd, switch_cmd)
        try:
            output = ssh_connectivity_check(
                switch_user, switch_password, ipadd, switch_cmd)
            output = subprocess.check_output(
                cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
            if output != None:
                output = output.decode('UTF-8').strip()
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output)
            else:
                exception = "Timeout"
                info = (
                    "Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                _info = info + ' ; ' + \
                    'command executed - {0}'.format(switch_cmd)
                os.system('logger -t montag -p user.info ' + info)
                # send_message_detailed(info, jid1, jid2, jid3)
                send_message_detailed(info, jid1, jid2, jid3)
                try:
                    mysql_save(runtime=runtime, ip_address=ipadd,
                               result='failure', reason=_info, exception=exception)
                except UnboundLocalError as error:
                    print(error)
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=_info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
        except subprocess.FileNotFoundError as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=_info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_network_loop_logs".format(
        date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = (
        "Preventive Maintenance Application - A loop has been detected on your network and the port {0} is administratively disabled on device {1}").format(port, ipadd)
    action = (
        "A Network Loop is noticed on OmniSwitch: {0} and we have deactivated the interface administratively").format(ipadd)
    result = (
        "Find enclosed to this notification the log collection of last 5 minutes and interface port {0} stauts").format(port)
    category = "network_loop"
    mysql_save(runtime=runtime, ip_address=ipadd,
               result='success', reason=action, exception='')
    return filename_path, subject, action, result, category


# Function to collect several command outputs related to Cloud-Agent (OV Cirrus) failure
def collect_command_output_ovc(switch_user, switch_password, decision, host, ipadd):
    """ 
    This function takes entries arguments the OmniSwitch IP Address where cloud-agent is enabled
    This function checks the decision received from Admin:
       if decision is 1, Administrator selected Yes and script disables the Cloud-Agent feature
       if decision is 0, Administrator selected No and we only provide command outputs  
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param int desicion:              Administrator decision (1: 'Yes', 0: 'No')
    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
    runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show cloud-agent status")
    if decision == "1":
        l_switch_cmd.append("cloud-agent admin-state disable force")
        l_switch_cmd.append("show cloud-agent status")

    for switch_cmd in l_switch_cmd:
        cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
            switch_password, switch_user, ipadd, switch_cmd)
        try:
            output = ssh_connectivity_check(
                switch_user, switch_password, ipadd, switch_cmd)
            output = subprocess.check_output(
                cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
            if output != None:
                output = output.decode('UTF-8').strip()
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output)
            else:
                exception = "Timeout"
                info = (
                    "Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                _info = info + ' ; ' + \
                    'command executed - {0}'.format(switch_cmd)
                os.system('logger -t montag -p user.info ' + info)
                # send_message_detailed(info, jid1, jid2, jid3)
                send_message_detailed(info, jid1, jid2, jid3)
                try:
                    mysql_save(runtime=runtime, ip_address=ipadd,
                               result='failure', reason=_info, exception=exception)
                except UnboundLocalError as error:
                    print(error)
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=_info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
        except subprocess.FileNotFoundError as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=_info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_ovc_logs".format(
        date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = (
        "Preventive Maintenance Application - Cloud-Agent module is into Invalid Status on OmniSwitch {0}").format(host)
    if decision == "1":
        action = (
            "The Cloud Agent feature is administratively disabled on OmniSwitch (Hostname: {0})").format(host)
        result = "Find enclosed to this notification the log collection of actions done"
    else:
        action = (
            "No action done on OmniSwitch (Hostname: {0}), please ensure the Serial Number is added in the OV Cirrus Device Catalog").format(host)
        result = "Find enclosed to this notification the log collection"
    category = "ovc"
    mysql_save(runtime=runtime, ip_address=ipadd,
               result='success', reason=action, exception='')
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
    runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show device-profile config")
    l_switch_cmd.append("show appmgr iot-profiler")

    for switch_cmd in l_switch_cmd:
        cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
            switch_password, switch_user, ipadd, switch_cmd)
        try:
            output = ssh_connectivity_check(
                switch_user, switch_password, ipadd, switch_cmd)
            output = subprocess.check_output(
                cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
            if output != None:
                output = output.decode('UTF-8').strip()
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output)
            else:
                exception = "Timeout"
                info = (
                    "Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                _info = info + ' ; ' + \
                    'command executed - {0}'.format(switch_cmd)
                os.system('logger -t montag -p user.info ' + info)
                # send_message_detailed(info, jid1, jid2, jid3)
                send_message_detailed(info, jid1, jid2, jid3)
                try:
                    mysql_save(runtime=runtime, ip_address=ipadd,
                               result='failure', reason=_info, exception=exception)
                except UnboundLocalError as error:
                    print(error)
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=_info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
        except subprocess.FileNotFoundError as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=_info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_mqtt_logs".format(
        date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = (
        "Preventive Maintenance Application - Device Profiling (aka IoT Profiling)  module is enabled on OmniSwitch {0} but unable to connect to OmniVista IP Address: {1}").format(host, ovip)
    action = (
        "No action done on OmniSwitch (Hostname: {0}), please check the IP connectivity with OmniVista, note that Device Profiling is not a VRF-aware feature").format(host)
    result = "Find enclosed to this notification the log collection"
    category = "mqtt"
    mysql_save(runtime=runtime, ip_address=ipadd,
               result='success', reason=action, exception='')
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
    runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show interfaces " + port + " status")
    l_switch_cmd.append("show interfaces " + port + " counters")
    l_switch_cmd.append("show interfaces " + port + " flood-rate")
    if decision == "1":
        l_switch_cmd.append("interfaces port " + port + " admin-state disable")
    l_switch_cmd.append("clear violation port " + port)
    l_switch_cmd.append("show violation")
    l_switch_cmd.append("show violation port " + port)

    for switch_cmd in l_switch_cmd:
        cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
            switch_password, switch_user, ipadd, switch_cmd)
        try:
            output = ssh_connectivity_check(
                switch_user, switch_password, ipadd, switch_cmd)
            output = subprocess.check_output(
                cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
            if output != None:
                output = output.decode('UTF-8').strip()
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output)
            else:
                exception = "Timeout"
                info = (
                    "Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                _info = info + ' ; ' + \
                    'command executed - {0}'.format(switch_cmd)
                os.system('logger -t montag -p user.info ' + info)
                # send_message_detailed(info, jid1, jid2, jid3)
                send_message_detailed(info, jid1, jid2, jid3)
                try:
                    mysql_save(runtime=runtime, ip_address=ipadd,
                               result='failure', reason=_info, exception=exception)
                except UnboundLocalError as error:
                    print(error)
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=_info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
        except subprocess.FileNotFoundError as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_storm_logs".format(
        date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = (
        "Preventive Maintenance Application - Unexpected traffic (storm) detected on switch: {0}, reason {1}").format(ipadd, source)
    if decision == "1":
        action = ("The Port {0} is administratively disabled on OmniSwitch (Hostname: {1})").format(
            port, host)
        result = "Find enclosed to this notification the log collection of actions done"
    else:
        action = ("No action done on OmniSwitch (Hostname: {0})").format(host)
        result = "Find enclosed to this notification the log collection"
    category = "storm"
    decision == "1"
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
    runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show interfaces " + port + " status")
    if decision == "1":
        l_switch_cmd.append("clear violation port " + port)
    l_switch_cmd.append("show violation")
    l_switch_cmd.append("show violation port " + port)

    for switch_cmd in l_switch_cmd:
        cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
            switch_password, switch_user, ipadd, switch_cmd)
        try:
            output = ssh_connectivity_check(
                switch_user, switch_password, ipadd, switch_cmd)
            output = subprocess.check_output(
                cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
            if output != None:
                output = output.decode('UTF-8').strip()
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output)
            else:
                exception = "Timeout"
                info = (
                    "Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                _info = info + ' ; ' + \
                    'command executed - {0}'.format(switch_cmd)
                os.system('logger -t montag -p user.info ' + info)
                # send_message_detailed(info, jid1, jid2, jid3)
                send_message_detailed(info, jid1, jid2, jid3)
                try:
                    mysql_save(runtime=runtime, ip_address=ipadd,
                               result='failure', reason=_info, exception=exception)
                except UnboundLocalError as error:
                    print(error)
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=_info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
        except subprocess.FileNotFoundError as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=_info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_violation_logs".format(
        date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = (
        "Preventive Maintenance Application - Port violation noticed on switch: {0}, reason {1}").format(ipadd, source)
    if decision == "1":
        action = ("The Port {0} is cleared from violation table on OmniSwitch (Hostname: {1})").format(
            port, host)
        result = "Find enclosed to this notification the log collection of actions done"
    else:
        action = ("No action done on OmniSwitch (Hostname: {0})").format(host)
        result = "Find enclosed to this notification the log collection"
    result = "Find enclosed to this notification the log collection of actions done"
    category = "violation"
    mysql_save(runtime=runtime, ip_address=ipadd,
               result='success', reason=action, exception='')
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
    runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show spb isis adjacency")
    l_switch_cmd.append("show spb isis interface")

    for switch_cmd in l_switch_cmd:
        cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
            switch_password, switch_user, ipadd, switch_cmd)
        try:
            output = ssh_connectivity_check(
                switch_user, switch_password, ipadd, switch_cmd)
            output = subprocess.check_output(
                cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
            if output != None:
                output = output.decode('UTF-8').strip()
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output)
            else:
                exception = "Timeout"
                info = (
                    "Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                _info = info + ' ; ' + \
                    'command executed - {0}'.format(switch_cmd)
                os.system('logger -t montag -p user.info ' + info)
                # send_message_detailed(info, jid1, jid2, jid3)
                send_message_detailed(info, jid1, jid2, jid3)
                try:
                    mysql_save(runtime=runtime, ip_address=ipadd,
                               result='failure', reason=_info, exception=exception)
                except UnboundLocalError as error:
                    print(error)
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=_info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
        except subprocess.FileNotFoundError as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=_info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_spb_logs".format(
        date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = (
        "Preventive Maintenance Application - SPB Adjacency issue detected on switch: {0}").format(ipadd)
    action = (
        "A SPB adjacency is down on OmniSwitch (Hostname: {0})").format(host)
    result = "Find enclosed to this notification the log collection for further analysis"
    category = "spb"
    mysql_save(runtime=runtime, ip_address=ipadd,
               result='success', reason=action, exception='')
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
    runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show powersupply")
    l_switch_cmd.append("show powersupply total")

    for switch_cmd in l_switch_cmd:
        cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
            switch_password, switch_user, ipadd, switch_cmd)
        try:
            output = ssh_connectivity_check(
                switch_user, switch_password, ipadd, switch_cmd)
            output = subprocess.check_output(
                cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
            if output != None:
                output = output.decode('UTF-8').strip()
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output)
            else:
                exception = "Timeout"
                info = (
                    "Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                _info = info + ' ; ' + \
                    'command executed - {0}'.format(switch_cmd)
                os.system('logger -t montag -p user.info ' + info)
                # send_message_detailed(info, jid1, jid2, jid3)
                send_message_detailed(info, jid1, jid2, jid3)
                try:
                    mysql_save(runtime=runtime, ip_address=ipadd,
                               result='failure', reason=_info, exception=exception)
                except UnboundLocalError as error:
                    print(error)
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=_info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
        except subprocess.FileNotFoundError as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=_info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_ps_logs".format(
        date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = (
        "Preventive Maintenance Application - Power Supply issue detected on switch: {0}").format(ipadd)
    action = ("The Power Supply unit {0} is down or running abnormal on OmniSwitch (Hostname: {1})").format(
        psid, host)
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
    runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show virtual-chassis vf-link")
    l_switch_cmd.append("show virtual-chassis auto-vf-link-port")
    l_switch_cmd.append("show virtual-chassis neighbors")
    l_switch_cmd.append("debug show virtual-chassis topology")

    for switch_cmd in l_switch_cmd:
        cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
            switch_password, switch_user, ipadd, switch_cmd)
        try:
            output = ssh_connectivity_check(
                switch_user, switch_password, ipadd, switch_cmd)
            output = subprocess.check_output(
                cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
            if output != None:
                output = output.decode('UTF-8').strip()
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output)
            else:
                exception = "Timeout"
                info = (
                    "Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                _info = info + ' ; ' + \
                    'command executed - {0}'.format(switch_cmd)
                os.system('logger -t montag -p user.info ' + info)
                # send_message_detailed(info, jid1, jid2, jid3)
                send_message_detailed(info, jid1, jid2, jid3)
                try:
                    mysql_save(runtime=runtime, ip_address=ipadd,
                               result='failure', reason=_info, exception=exception)
                except UnboundLocalError as error:
                    print(error)
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=_info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
        except subprocess.FileNotFoundError as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=_info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_vcmm_logs".format(
        date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = (
        "Preventive Maintenance Application - Virtual Chassis issue detected on switch: {0}").format(ipadd)
    action = ("The VC CMM {0} is down on VC (Hostname: {1}) syslogs").format(
        vcid, host)
    result = "Find enclosed to this notification the log collection for further analysis"
    category = "vcmm"
    mysql_save(runtime=runtime, ip_address=ipadd,
               result='success', reason=action, exception='')
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
    runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show interfaces alias")
    l_switch_cmd.append("show linkagg")
    l_switch_cmd.append("show linkagg agg " + agg)
    l_switch_cmd.append("show linkagg agg " + agg + " port")

    for switch_cmd in l_switch_cmd:
        cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
            switch_password, switch_user, ipadd, switch_cmd)
        try:
            output = ssh_connectivity_check(
                switch_user, switch_password, ipadd, switch_cmd)
            output = subprocess.check_output(
                cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
            if output != None:
                output = output.decode('UTF-8').strip()
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output)
            else:
                exception = "Timeout"
                info = (
                    "Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                _info = info + ' ; ' + \
                    'command executed - {0}'.format(switch_cmd)
                os.system('logger -t montag -p user.info ' + info)
                # send_message_detailed(info, jid1, jid2, jid3)
                send_message_detailed(info, jid1, jid2, jid3)
                try:
                    mysql_save(runtime=runtime, ip_address=ipadd,
                               result='failure', reason=_info, exception=exception)
                except UnboundLocalError as error:
                    print(error)
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=_info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
        except subprocess.FileNotFoundError as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=_info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_linkagg_logs".format(
        date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = (
        "Preventive Maintenance Application - Linkagg issue detected on switch: {0}").format(ipadd)
    action = ("A Linkagg issue has been detected in switch(Hostname: {0}) Aggregate {1}").format(
        host, agg)
    result = "Find enclosed to this notification the log collection for further analysis"
    category = "linkagg"
    return filename_path, subject, action, result, category

# Function to collect several command outputs related to PoE

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
    l_switch_cmd.append("show interfaces alias")
    # l_switch_cmd.append("show interfaces alias; show system; show lldp remote-system; show configuration snapshot lanpower; \
    #    show powersupply total; show lanpower slot 1/1 ; show lanpower slot 1/1 port-config; show lanpower power-rule; show lanpower chassis 1 capacitor-detection; \
    #    show lanpower chassis 1 usage-threshold; show lanpower chassis 1 ni-priority; show lanpower slot 1/1 high-resistance-detection; \
    #    show lanpower slot 1/1 priority-disconnect; show lanpower slot 1/1 class-detection")
    print(ipadd)
    for switch_cmd in l_switch_cmd:
        try:
            output = ssh_connectivity_check(
                switch_user, switch_password, ipadd, switch_cmd)
            print(output)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '", "")
                output_decode = output_decode.replace("']", "")
                output_decode = output_decode.replace("['", "")
                print(output_decode)
                text = "{0}{1}: \n{2}\n\n".format(
                    text, switch_cmd, output_decode)
            else:
                exception = "Timeout"
                info = (
                    "Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)

                os.system('logger -t montag -p user.info ' + info)
                send_message_detailed(info, jid1, jid2, jid3)
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)

            os.system('logger -t montag -p user.info ' + info)
            send_message_detailed(info, jid1, jid2, jid3)
            sys.exit()
        except subprocess.SubprocessError as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)

            os.system('logger -t montag -p user.info ' + info)
            send_message_detailed(info, jid1, jid2, jid3)
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_poe_logs".format(
        date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (path + '{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    lanpower_settings_status = 0
    switch_cmd = "show configuration snapshot lanpower"
    try:
        output = ssh_connectivity_check(
            switch_user, switch_password, ipadd, switch_cmd)

        if output != None:
            output = str(output)
            output_decode = bytes(output, "utf-8").decode("unicode_escape")
            output_decode = output_decode.replace("', '", "")
            output_decode = output_decode.replace("']", "")
            lanpower_settings_status = output_decode.replace("['", "")
            #lanpower_settings_status = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
            #lanpower_settings_status = lanpower_settings_status.decode('UTF-8').strip()
            print(lanpower_settings_status)
    except subprocess.TimeoutExpired as exception:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)

        os.system('logger -t montag -p user.info ' + info)
        send_message_detailed(info, jid1, jid2, jid3)
        sys.exit()
    except subprocess.SubprocessError as exception:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)

        os.system('logger -t montag -p user.info ' + info)
        send_message_detailed(info, jid1, jid2, jid3)
        sys.exit()
    print("je suis passe ici")
    print(lanpower_settings_status)
    capacitor_detection_status = high_resistance_detection_status = "disabled"
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
    print(reason)
    if reason == "(Illegal class)":
        subject = (
            "Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port 1/1/{2} - reason: {3}").format(host, ipadd, port, reason)
        action = ("A PoE issue has been detected in switch(Hostname : {0}) syslogs with reason {1}. The OmniSwitch POE controller requires that the same class be detected on both pairs before passing detection and sending POE power to the port. When it detects different classes from the same device, power is denied until 4pair is disabled").format(
            host, reason)
        result = "Find enclosed to this notification the log collection for further analysis"
    elif reason == "Fail due to out-of-range capacitor value" or reason == "Port is off: Voltage injection into the port (Port fails due to voltage being applied to the port from external source)" and high_resistance_detection_status == "enabled":
        subject = (
            "Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port 1/1/{2} - reason: {3}").format(host, ipadd, port, reason)
        action = ("A PoE issue has been detected in switch(Hostname : {0}) syslogs. High Resistance Detection is {1}. Please disable the high-resistance-detection (lanpower slot x/1 high-resistance-detection disable) if not necessary or disable the Lanpower on port that are non Powered Devices (lanpower port x/x/x admin-state disable)").format(
            host, high_resistance_detection_status)
        result = "Find enclosed to this notification the log collection for further analysis"
    elif reason == "Fail due to out-of-range capacitor value" or reason == "Port is off: Voltage injection into the port (Port fails due to voltage being applied to the port from external source)" and capacitor_detection_status == "enabled":
        subject = (
            "Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port 1/1/{2} - reason: {3}").format(host, ipadd, port, reason)
        action = ("A PoE issue has been detected in switch(Hostname : {0}) syslogs. Capacitor Detection is {1}. Please disable the capacitor-detection (lanpower slot x/1 capacitor-detection disable)  if not necessary or disable the Lanpower on port that are non Powered Devices (lanpower port x/x/x admin-state disable)").format(
            host, capacitor_detection_status)
        result = "Find enclosed to this notification the log collection for further analysis"
    elif reason == "Port is off: Voltage injection into the port (Port fails due to voltage being applied to the port from external source)":
        subject = (
            "Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port 1/1/{2} - reason: {3}").format(host, ipadd, port, reason)
        action = (
            "A PoE issue has been detected in switch(Hostname : {0}) syslogs. Please disable the Lanpower on port that are non Powered Devices (lanpower port x/x/x admin-state disable)").format(host)
        result = "Find enclosed to this notification the log collection for further analysis"
    elif reason == "Port is off: Over temperature at the port (Port temperature protection mechanism was activated)" or reason == "(Port temperature protection mechanism was activated)":
        subject = (
            "Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port 1/1/{2} - reason: {3}").format(host, ipadd, port, reason)
        action = (
            "A PoE issue has been detected in switch(Hostname : {0}) syslogs. Please upgrade the switch to AOS 8.7R03 for supporting latest Lanpower APIs and monitor. If issue still persists, try a reload of Lanpower (lanpower slot x/x service stop; lanpower slot x/x service start)").format(host)
        result = "Find enclosed to this notification the log collection for further analysis"
    elif reason == "Non-standard PD connected":
        subject = (
            "Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port 1/1/{2} - reason: {3}").format(host, ipadd, port, reason)
        action = (
            "A PoE issue has been detected in switch(Hostname : {0}) syslogs. A non-powered device is connected to PoE port, please disable the lanpower on this port if you want to remove this error message (lanpower port x/x/x admin-state disable)").format(host)
        result = "Find enclosed to this notification the log collection for further analysis"
    elif reason == "Port is off: Overload state (Overload state according to 802.3AF/AT, current is above Icut)":
        subject = (
            "Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port 1/1/{2} - reason: {3}").format(host, ipadd, port, reason)
        action = (
            "A PoE issue has been detected in switch(Hostname : {0}) syslogs and port is in Denied State. This issue is fixed in AOS 8.6R02. If issue still persists, try a reload of Lanpower (lanpower slot x/x service stop; lanpower slot x/x service start)").format(host)
        result = "Find enclosed to this notification the log collection for further analysis"
    elif reason == "Port is yet undefined (Getting this status means software problem)" or reason == "Internal hardware fault (Port does not respond, hardware fault, or system initialization)":
        subject = (
            "Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port 1/1/{2} - reason: {3}").format(host, ipadd, port, reason)
        action = (
            "A PoE issue has been detected in switch(Hostname : {0}) syslogs. Please collect logs and contact ALE Customer Support").format(host)
        result = "Find enclosed to this notification the log collection for further analysis"
    elif reason == "Port is off: Power budget exceeded (Power Management function shuts down port, due to lack of power. Port is shut down or remains off)":
        subject = (
            "Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port 1/1/{2} - reason: {3}").format(host, ipadd, port, reason)
        action = ("A PoE issue has been detected in switch(Hostname : {0}) syslogs and port is in Denied State. Please verify the Active Bank is compliant with your OmniSwitch model. If Switch model is OS6860N-P48 please ensure the latest CPLD firmware is applied, more details on Technical Knowledge Base  https://myportal.al-enterprise.com/alebp/s/tkc-redirect?000066680.").format(host)
        result = "Find enclosed to this notification the log collection for further analysis"
    elif reason == "Port is off: Main supply voltage is low (Mains voltage is lower than Min Voltage limit)":
        subject = (
            "Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port 1/1/{2} - reason: {3}").format(host, ipadd, port, reason)
        action = (
            "A PoE issue has been detected in switch(Hostname : {0}) syslogs and port is in Denied State. Please collect logs and contact ALE Customer Support. If Switch model is OS6465H-P6 or OS6465H-P12 with a power supply 75W/48V: only 802.3at Powered Devices are supported.").format(host)
        result = "Find enclosed to this notification the log collection for further analysis"
    else:
        subject = (
            "Preventive Maintenance Application - Lanpower issue detected on OmniSwitch: {0}/{1} - port 1/1/{2} - reason: {3}").format(host, ipadd, port, reason)
        action = (
            "A PoE issue has been detected in switch(Hostname : {0}) syslogs. Please collect logs and contact ALE Customer Support").format(host)
        result = "Find enclosed to this notification the log collection for further analysis"
    category = "poe"
    return filename_path, subject, action, result, category, capacitor_detection_status, high_resistance_detection_status

def collect_command_output_ddm(switch_user, switch_password, host, ipadd, port, slot, ddm_type, threshold, sfp_power):
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
    text = "More logs related to the Digital Diagnostics Monitoring (DDM) noticed on OmniSwitch: {0} \n\n\n".format(
        ipadd)
    text = "########################################################################"

    l_switch_cmd = []
    l_switch_cmd.append(
        ("show system; show transceivers slot {0}/1; show interfaces; show interfaces status; show lldp remote-system").format(slot))

    for switch_cmd in l_switch_cmd:
        try:
            output = ssh_connectivity_check(
                switch_user, switch_password, ipadd, switch_cmd)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '", "")
                output_decode = output_decode.replace("']", "")
                output_decode = output_decode.replace("['", "")
                text = "{0}{1}: \n{2}\n\n".format(
                    text, switch_cmd, output_decode)
            else:
                exception = "Timeout"
                info = (
                    "Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)

                os.system('logger -t montag -p user.info ' + info)
                send_message_detailed(info, jid1, jid2, jid3)
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)

            os.system('logger -t montag -p user.info ' + info)
            send_message_detailed(info, jid1, jid2, jid3)
            sys.exit()
        except subprocess.SubprocessError as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)

            os.system('logger -t montag -p user.info ' + info)
            send_message_detailed(info, jid1, jid2, jid3)
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_ddm_logs".format(
        date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (path + '{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = (
        "Preventive Maintenance Application - The SFP on OmniSwitch: {0}/{1} - crossed DDM (Digital Diagnostics Monitoring) threshold").format(host, ipadd)
    action = ("The SFP {0}/{1} on OmniSwitch {2}/{3} crossed DDM (Digital Diagnostics Monitoring) threshold {4} {5}: {6}").format(
        slot, port, host, ipadd, threshold, ddm_type, sfp_power)
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
    runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
    service_status = 0
    protocol_a = 0
    if protocol == "HTTPS":
        protocol_a == "http"
    switch_cmd = "show ip service | grep {0}".format(protocol_a)
    cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
        switch_password, switch_user, ipadd, switch_cmd)
    try:
        service_status = subprocess.check_output(
            cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
        service_status = service_status.decode('UTF-8').strip()
        print(service_status)
    except subprocess.TimeoutExpired as exception:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
        os.system('logger -t montag -p user.info ' + info)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,
                       result='failure', reason=_info, exception=exception)
        except UnboundLocalError as error:
            print(error)
        sys.exit()
    except AttributeError as exception:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
        os.system('logger -t montag -p user.info ' + info)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,
                       result='failure', reason=_info, exception=exception)
        except UnboundLocalError as error:
            print(error)
        sys.exit()
    except FileNotFoundError as exception:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
        os.system('logger -t montag -p user.info ' + info)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,
                       result='failure', reason=_info, exception=exception)
        except UnboundLocalError as error:
            print(error)
        sys.exit()
    if "enabled" in service_status:
        print("Protocol " + protocol + " enabled!")
        service_status = "enabled"
    else:
        service_status = "disabled"

    switch_cmd = "show configuration snapshot aaa | grep \"aaa authentication {0}\"".format(
        protocol)
    cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
        switch_password, switch_user, ipadd, switch_cmd)
    try:
        aaa_status = subprocess.check_output(
            cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
        aaa_status = aaa_status.decode('UTF-8').strip()
        print(aaa_status)
        if "aaa authentication" in aaa_status:
            aaa_status = "enabled"
    except subprocess.TimeoutExpired as exception:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
        os.system('logger -t montag -p user.info ' + info)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,
                       result='failure', reason=_info, exception=exception)
        except UnboundLocalError as error:
            print(error)
        sys.exit()
    except subprocess.CalledProcessError as e:
        aaa_status = "disabled"
    except AttributeError as exception:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
        os.system('logger -t montag -p user.info ' + info)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,
                       result='failure', reason=_info, exception=exception)
        except UnboundLocalError as error:
            print(error)
        sys.exit()
    except FileNotFoundError as exception:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
        os.system('logger -t montag -p user.info ' + info)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,
                       result='failure', reason=_info, exception=exception)
        except UnboundLocalError as error:
            print(error)
        sys.exit()

    print(aaa_status)
    mysql_save(runtime=runtime, ip_address=ipadd, result='success',
               reason="The python script execution on OmniSwitch {0}".format(ipadd), exception='')
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
    runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append("show ip service")
    l_switch_cmd.append("show aaa authentication")

    for switch_cmd in l_switch_cmd:
        cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
            switch_password, switch_user, ipadd, switch_cmd)
        try:
            output = ssh_connectivity_check(
                switch_user, switch_password, ipadd, switch_cmd)
            output = subprocess.check_output(
                cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
            if output != None:
                output = output.decode('UTF-8').strip()
                text = "{0}{1}: \n{2}\n\n".format(text, switch_cmd, output)
            else:
                exception = "Timeout"
                info = (
                    "Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)
                print(info)
                _info = info + ' ; ' + \
                    'command executed - {0}'.format(switch_cmd)
                os.system('logger -t montag -p user.info ' + info)
                # send_message_detailed(info, jid1, jid2, jid3)
                send_message_detailed(info, jid1, jid2, jid3)
                try:
                    mysql_save(runtime=runtime, ip_address=ipadd,
                               result='failure', reason=_info, exception=exception)
                except UnboundLocalError as error:
                    print(error)
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=_info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
        except subprocess.FileNotFoundError as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
            print(info)
            _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
            os.system('logger -t montag -p user.info ' + info)
            # send_message_detailed(info, jid1, jid2, jid3)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd,
                           result='failure', reason=_info, exception=exception)
            except UnboundLocalError as error:
                print(error)
            sys.exit()
    date = datetime.date.today()
    date_hm = datetime.datetime.today()

    filename = "{0}_{1}-{2}_{3}_authentication_logs".format(
        date, date_hm.hour, date_hm.minute, ipadd)
    filename_path = (path + '/{0}.txt').format(filename)
    f_logs = open(filename_path, 'w')
    f_logs.write(text)
    f_logs.close()
    subject = (
        "Preventive Maintenance Application - Authentication failure noticed on switch: {0}").format(ipadd)
    action = ("An Authentication failure has been detected in switch( Hostname: {0} ) from User: {1} - source IP Address: {2} - protocol: {3}").format(
        host, user, source_ip, protocol)
    result = ("As per configuration, this service protocol is {0} and aaa authentication is {1}").format(
        service_status, aaa_status)
    category = "authentication"
    mysql_save(runtime=runtime, ip_address=ipadd,
               result='success', reason=action, exception='')
    return filename_path, subject, action, result, category

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


def script_has_run_recently(seconds, ip, function):
    """ 
    This function is called on scenario when we prevent to run the script again and again because we receive remanent logs or further logs after 1st notification was sent
    :param str seconds:              Runtime
    :param str ip:                   Switch IP Address
    :param str function:             Which use case: loop, flapping
    :return:                         True (if runtime less than 5 minutes) or False
    """
    filename = (path + '/last-runtime_{0}.txt').format(function)
    current_time = int(time.time())
    text = "{0},{1},{2}\n".format(str(current_time), ip, function)
    try:
        content = open(
            path + "/last-runtime_{0}.txt".format(function), "r", errors='ignore')
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
            print(
                "IP Address and function found in last-runtime + last run less than 5 minutes")
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
    content = open(
        "/opt/ALE_Script/last-runtime_{0}.txt".format(function), "r", errors='ignore')
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


def port_monitoring(switch_user, switch_password, port, ipadd):
    """ 
    This function executes a port monitoring (packet capture) on port received in argument  
    This function returns file path containing the show command outputs and the notification subject, body used when calling VNA API

    :param str port:                  Switch Interface/Port ID <chasis>/<slot>/>port>
    :param str host:                  Switch Hostname
    :param str ipadd:                 Switch IP address
    :return:                          filename_path,subject,action,result,category
    """
   # Execute port monitoring on port with subprocess.call as we are not expecting output
    switch_cmd = ("port-monitoring 1 source port " + port +
                  " file /flash/pmonitor.enc size 1 timeout 30 inport capture-type full enable")
    cmd = "sshpass -p {0} ssh -o StrictHostKeyChecking=no  {1}@{2} {3}".format(
        switch_password, switch_user, ipadd, switch_cmd)
    try:
        output = subprocess.call(
            cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
        print(output)
        return True
    except subprocess.SubprocessError:
        print("Issue when executing command")

def isEssential(addr):
    """
    Check if IP addr is in Esssential_ip.csv file
    return: True if addr is in file else False
    """
    ips_address = list()
    with open(path + "/Essential_ip.csv") as csv_file:
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
            output = ssh_connectivity_check(
                switch_user, switch_password, ipadd, switch_cmd)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '", "")
                output_decode = output_decode.replace("']", "")
                output_vlan_members = output_decode.replace("['", "")
            else:
                exception = "Timeout"
                info = (
                    "Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)

                os.system('logger -t montag -p user.info ' + info)
                send_message_detailed(info, jid1, jid2, jid3)
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)

            os.system('logger -t montag -p user.info ' + info)
            send_message_detailed(info, jid1, jid2, jid3)
        except subprocess.SubprocessError as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)

            os.system('logger -t montag -p user.info ' + info)
            send_message_detailed(info, jid1, jid2, jid3)
            sys.exit()
        # if port is member of a linkagg ERROR is displayed in output
        if re.search(r"ERROR", output_vlan_members):
            return True
        else:
            # if port is member of more than 2 VLAN tagged
            qtagged = re.findall(r"qtagged", output)
            if len(qtagged) > 1:
                return True
            else:
                return False

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
    runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

    switch_cmd = "show lldp port {0} remote-system".format(port)
    try:
        output = ssh_connectivity_check(
            switch_user, switch_password, ipadd, switch_cmd)
        print(output)
        if output != None:
            output = str(output)
            output_decode = bytes(output, "utf-8").decode("unicode_escape")
            output_decode = output_decode.replace("', '", "")
            output_decode = output_decode.replace("']", "")
            lldp_port = output_decode.replace("['", "")
    except subprocess.TimeoutExpired as exception:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        os.system('logger -t montag -p user.info ' + info)
        _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,
                       result='failure', reason=_info, exception=exception)
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass
        sys.exit()
    except AttributeError as exception:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
        os.system('logger -t montag -p user.info ' + info)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,
                       result='failure', reason=_info, exception=exception)
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass
        sys.exit()
    except FileNotFoundError as exception:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
        os.system('logger -t montag -p user.info ' + info)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,
                       result='failure', reason=_info, exception=exception)
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass
        sys.exit()
    if "Port Description" in lldp_port:
        try:
            print(lldp_port)
            lldp_port_description = re.findall(
                r"Port Description            = (.*?),", lldp_port)[0]
            lldp_mac_address = re.findall(r"Port (.*?):\n", lldp_port)[1]
            mysql_save(runtime=runtime, ip_address=ipadd, result='success',
                       reason=lldp_port_description, exception='')
        except:
            lldp_port_description = lldp_mac_address = 0
            pass
    return lldp_port_description, lldp_mac_address


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
    # Log collection of additionnal command outputs
    text = "More logs about the switch : {0} \n\n\n".format(ipadd)

    l_switch_cmd = []
    l_switch_cmd.append(("show interfaces port {0}").format(port))

    for switch_cmd in l_switch_cmd:
        try:
            output = ssh_connectivity_check(
                switch_user, switch_password, ipadd, switch_cmd)
            if output != None:
                output = str(output)
                output_decode = bytes(output, "utf-8").decode("unicode_escape")
                output_decode = output_decode.replace("', '", "")
                output_decode = output_decode.replace("']", "")
                output_decode = output_decode.replace("['", "")
                text = "{0}{1}: \n{2}\n\n".format(
                    text, switch_cmd, output_decode)
            else:
                exception = "Timeout"
                info = (
                    "Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ipadd)

                os.system('logger -t montag -p user.info ' + info)
                send_message_detailed(info, jid1, jid2, jid3)
                try:
                    mysql_save(runtime=runtime, ip_address=ipadd, result='failure',
                               reason="CommandExec", exception=exception)
                except UnboundLocalError as error:
                    print(error)
                except Exception as error:
                    print(error)
                    pass
                sys.exit()
        except subprocess.TimeoutExpired as exception:
            info = (
                "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)

            os.system('logger -t montag -p user.info ' + info)
            send_message_detailed(info, jid1, jid2, jid3)
            try:
                mysql_save(runtime=runtime, ip_address=ipadd, result='failure',
                           reason="CommandExec", exception=exception)
            except UnboundLocalError as error:
                print(error)
            except Exception as error:
                print(error)
                pass
            sys.exit()
        status_changes = re.findall(
            r"Number of Status Change   : (.*?),", output_decode)[0]
        link_quality = re.findall(
            r"Link-Quality              : (.*?),", output_decode)[0]
    return status_changes, link_quality


def collect_command_output_lldp_port_capability(switch_user, switch_password, port, ipadd):
    """ 
    This function takes IP Address and port as argument. This function is called when we want additionnal information on equipment connected to Switch Interface
    This function returns LLDP Port Capability field value
    :param str port:                      Switch Interface Port
    :param str ipadd:                     Switch IP address
    :return:                              lldp_capability
    """
    lldp_port_capability = 0
    switch_cmd = "show lldp port {0} remote-system".format(port)
    try:
        output = ssh_connectivity_check(
            switch_user, switch_password, ipadd, switch_cmd)
        if output != None:
            output = str(output)
            output_decode = bytes(output, "utf-8").decode("unicode_escape")
            output_decode = output_decode.replace("', '", "")
            output_decode = output_decode.replace("']", "")
            lldp_port = output_decode.replace("['", "")
    except subprocess.TimeoutExpired as exception:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)

        os.system('logger -t montag -p user.info ' + info)
        send_message_detailed(info, jid1, jid2, jid3)
        sys.exit()
    except AttributeError as exception:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)

        os.system('logger -t montag -p user.info ' + info)
        send_message_detailed(info, jid1, jid2, jid3)
        sys.exit()
    except FileNotFoundError as exception:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)

        os.system('logger -t montag -p user.info ' + info)
        send_message_detailed(info, jid1, jid2, jid3)
        sys.exit()
    if "Port Description" in lldp_port:
        try:
            lldp_port_capability = re.findall(
                r"Capabilities Supported      = (.*?),", lldp_port)[0]
            lldp_mac_address = re.findall(r"Port (.*?):\n", lldp_port)[1]
        except exception as error:
            print(error)
            lldp_port_capability = 0
            pass
    return lldp_port_capability


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
    runtime = strftime("%Y-%m-%d %H:%M:%S", localtime())

    switch_cmd = "show arp | grep \"{0}\"".format(lldp_mac_address)
    try:
        output = ssh_connectivity_check(
            switch_user, switch_password, ipadd, switch_cmd)
        print(output)
        if output != None:
            output = str(output)
            output_decode = bytes(output, "utf-8").decode("unicode_escape")
            output_decode = output_decode.replace("', '", "")
            output_decode = output_decode.replace("']", "")
            device_ip = output_decode.replace("['", "")
    except subprocess.TimeoutExpired as exception:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
        os.system('logger -t montag -p user.info ' + info)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3,
                              'Get ARP Entry', 'Status: Failure', company)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,
                       result='failure', reason=_info, exception=exception)
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass
        sys.exit()
    except AttributeError as exception:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
        os.system('logger -t montag -p user.info ' + info)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3,
                              'Get ARP Entry', 'Status: Failure', company)
        try:
            mysql_save(runtime=runtime, ip_address=ipadd,
                       result='failure', reason=_info, exception=exception)
        except UnboundLocalError as error:
            print(error)
        except Exception as error:
            print(error)
            pass
        sys.exit()
    except FileNotFoundError as exception:
        info = (
            "The python script execution on OmniSwitch {0} failed - {1}").format(ipadd, exception)
        print(info)
        _info = info + ' ; ' + 'command executed - {0}'.format(switch_cmd)
        os.system('logger -t montag -p user.info ' + info)
        # send_message_detailed(info, jid1, jid2, jid3)
        send_message_detailed(info, jid1, jid2, jid3,
                              'Get ARP Entry', 'Status: Failure', company)
        sys.exit()
    try:
        if "{0}".format(lldp_mac_address) in device_ip:
            print(device_ip)
            device_ip = re.findall(
                r" ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}) ", device_ip)[0]
        else:
            print("No ARP Entry for this MAC Address")
    except:
        pass
    print(device_ip)
    return device_ip

# Function to enable syslogs on OmniSwitches when Setup.sh is called


def enable_syslog(switch_user, switch_password, ipadd, port):
    """ 
    This function takes entries arguments the OmniSwitch IP Address from Devices.csv file, the OmniSwitch credentials, the syslog port to be used
    Note that VRF is not supported, syslog are enabled on the default VRF

    :param str ipadd:                 OmniSwitch IP Address
    :param str port:                  Syslog Port (default 10514)
    :script executed ssh_device:      with cmd in argument
    :return:                          None
    """

    cmd = ("swlog output socket {0} {1}").format(ipadd, port)
    ssh_connectivity_check(switch_user, switch_password, ipadd, cmd)


if __name__ == "__main__":
    login_switch, pass_switch, mails, rainbow_jid1, rainbow_jid2, rainbow_jid3, ip_server_log, login_AP, pass_AP, tech_pass, random_id, company, room_id = get_credentials()
    print("d")
else:
    print("Support_Tools_OmniSwitch Script called by another script")
