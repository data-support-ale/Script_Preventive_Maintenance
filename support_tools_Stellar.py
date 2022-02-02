#!/usr/bin/env python

import sys
import os
import logging
import datetime
from support_send_notification import send_message
import subprocess
import re
import requests
import paramiko
import glob

date = datetime.date.today()
date_hm = datetime.datetime.today()

# This script contains all functions interacting with Stellar APs

# Function SSH for checking connectivity before collecting logs


def ssh_connectivity_check(ipadd, cmd):
    """ 
    This function takes entry the command to push remotely on Stellar AP by SSH with Python Paramiko module
    Paramiko exceptions are handled for notifying Network Administrator if the SSH Session does not establish

    :param str ipadd                  Stellar AP IP Address
    :param str cmd                    Command pushed by SSH on Stellar AP
    :return:  stdout, stderr          If exceptions is returned on stderr a notification is sent to Network Administrator, else we log the session was established
    """
    print(cmd)
    try:
        p = paramiko.SSHClient()
        p.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        p.connect(ipadd, port=22, username=ap_user, password=ap_password)
    except paramiko.ssh_exception.AuthenticationException:
        print("Authentication failed enter valid user name and password")
        info = (
            "SSH Authentication failed when connecting to Stellar AP {0}, we cannot collect logs").format(ipadd)
        os.system('logger -t montag -p user.info {0}').format(info)
        send_message(info, jid)
        sys.exit(0)
    except paramiko.ssh_exception.NoValidConnectionsError:
        print("Device unreachable")
        logging.info(
            runtime + ' SSH session does not establish on Stellar AP ' + ipadd)
        info = ("Stellar AP {0} is unreachable, we cannot collect logs").format(
            ipadd)
        os.system('logger -t montag -p user.info {0}').format(info)
        send_message(info, jid)
        sys.exit(0)
    stdin, stdout, stderr = p.exec_command(cmd)
    exception = stderr.readlines()
    exception = str(exception)
    print(stdout)
    print(exception)
    cmd = "sshpass -p {0} ssh -v -o StrictHostKeyChecking=no {1}@{2} genrpd {3}".format(
        ap_password, ap_user, ipadd, "Letacla01*")
    run = cmd.split()
    p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=None)
    stdout, stderr = p.communicate()
    pass_root = stdout.decode('ascii').strip()
    print(pass_root)
    return pass_root


# Function SSH for checking connectivity before collecting logs
def get_snapshot_tftp(pass_root, ipadd):
    """ 
    This function takes entry the Stellar AP IP Address to execute by SSH the snapshot log collection
    Paramiko exceptions are handled for notifying Network Administrator if the SSH Session does not establish
    This function returns file path containing the snapshot log file and the notification subject, body used when calling VNA API

    :param str ipadd                             Command pushed by SSH on Stellar AP
    :param str cmd                               Command pushed by SSH on Stellar AP
    :return:  stdout, stderr, pass_root          If exceptions is returned on stderr a notification is sent to Network Administrator, else we log the session was established and we return the filename_path,subject,action,result,category
    """
    cmd = "/usr/sbin/take_snapshot.sh start 10.130.7.14"
    os.system(
        "sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  root@{1} {2}".format(pass_root, ipadd, cmd))
    cmd = "/usr/sbin/getmac"
    cmd = "sshpass -p '{0}' ssh -v  -o StrictHostKeyChecking=no  root@{1} {2}".format(
        pass_root, ipadd, cmd)
    output = subprocess.check_output(
        cmd, stderr=subprocess.DEVNULL, timeout=40, shell=True)
    ap_mac = output.decode('UTF-8').strip()
    ap_mac = ap_mac.replace(":", "")
    ap_mac = ("{0}_snapshot_{1}{2}").format(ap_mac, date, date_hm.hour)
    ap_mac = ap_mac.replace("-", "")
    list_of_files = glob.glob('/tftpboot/{0}*'.format(ap_mac))
    paths_str = max(list_of_files, key=os.path.getctime)
    print(paths_str)
    print(paths_str)
    return paths_str


def send_file(filename_path, subject, action, result):
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
    response = "<Response [200]>"
    response = re.findall(r"<Response \[(.*?)\]>", response)
    if "200" in response:
        os.system('logger -t montag -p user.info 200 OK')
    else:
        os.system('logger -t montag -p user.info REST API Call Failure')


if __name__ == "__main__":
    jid = "570e12872d768e9b52a8b975@openrainbow.com"
    ap_password = "Letacla01*"
    ap_user = "support"
    ipadd = "10.130.7.76"
    cmd = "/usr/sbin/showsysinfo"
    host = "10.130.7.76"
    pass_root = ssh_connectivity_check(ap_user, ap_password, ipadd, cmd)
    get_snapshot_tftp(pass_root, ipadd)
