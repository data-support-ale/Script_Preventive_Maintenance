#!/usr/local/bin/python3.7

from argparse import Action
from distutils.log import info
import sys
import os
import json
import datetime
from time import strftime, localtime, time
from support_tools_OmniSwitch import get_credentials, send_file, ssh_connectivity_check, execute_command, port_monitoring, get_file_sftp
from support_send_notification import send_message
from database_conf import *
import re
import paramiko
import pexpect

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

date = datetime.date.today()
date_hm = datetime.datetime.today()

def printchild(child, out):
    temp = b''
    #require extra empty CLI for correct output
    child.sendline ("")
    child.expect ("->") #carefull with expect prompt output from CLI. Each system may difference
    temp = child.before
    out += temp.decode("utf-8")
    return out

def cmd(child, cmds, expt, timeout):
    temp= b''
    cmdout=''
    child.expect(expt, timeout=timeout)
    child.sendline(cmds)
    cmdout += printchild(child, cmdout)
    return cmdout

def entry_log(log,function,ipadd):
  """ 
  This function permit the collection of script logs
  :param str old_log:           The entire log string
  :param str portnumber:        The new entry in logs string
  :return:                      None

  """
  logfilename = strftime('%Y-%m-%d', localtime(time())) + "_lastlog_saa_{0}_{1}.log".format(function,ipadd)
  logfilepath = "/var/log/devices/{0}".format(logfilename)
  #path = os.getcwd()
  print(log)
  with open(logfilepath, "a") as file:
     file.write("{0}: {1}\n".format(datetime.datetime.now(),log))
  return logfilepath

last = ""
with open("/var/log/devices/lastlog_saa.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_saa.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_saa.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_saa.json empty")
        exit()
    except IndexError:
        print("Index error in regex")
        exit()
    
    ipadd_list = ['10.130.7.244', '10.130.7.245', '10.130.7.246']

    # Sample log
    # OS6900_VC swlogd saaCmm sm-proto INFO: SPB:SPB-500-e8-e7-32-cc-f3-4f - Iteration packet loss 4/0
    if "Iteration packet loss" in msg:
        ##### Port monitoring to check if frames are received with VLAN Tag 4095 #####
        try:
            port = "2/1/6"
            ip = "10.130.7.245"
            port_monitoring(switch_user, switch_password, port, ip)
        except:
            info = "Service Assurance Agent - Port Monitoring failed"
            send_message(info,jid)
            pass
        try:
            saa_name = re.findall(r"INFO: (.*?) - Iteration packet loss", msg)[0]
            info = ("Service Assurance Agent - SAA probe {0} configured on OmniSwitch {1} / {2} failed").format(saa_name,ipadd,host)
            send_message(info,jid)

            l_switch_cmd = []
            l_switch_cmd.append("show system; show chassis; show spb isis nodes; show spb isis adjacency; show spb isis bvlans; show spb isis unicast-table \
            show spb isis spf bvlan 200; show spb isis spf bvlan 300; show spb isis spf bvlan 400; show spb isis spf bvlan 500; show spb isis spf bvlan 600 \
            show service spb; show spb isis services; show service access; show service 2 debug-info; show service 3 debug-info; show service 4 debug-info \
            show service 5 debug-info; show service 6 debug-info; show service 32000 debug-info; show unp user")

            for switch_cmd in l_switch_cmd:
                for ipadd in ipadd_list:
                    try:
                        output = ssh_connectivity_check(switch_user, switch_password, ipadd, switch_cmd)
                        if output != None:
                            output = str(output)
                            output_decode = bytes(output, "utf-8").decode("unicode_escape")
                            output_decode = output_decode.replace("', '","")
                            output_decode = output_decode.replace("']","")
                            output_decode = output_decode.replace("['","")
                            print(output_decode)
                            entry_log(output_decode,"CLI",ipadd)
                            
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

                    except Exception as error:
                        print(error)
                    pass 

            l_switch_cmd = []
            l_switch_cmd.append("d chg ING_DVP_TABLE;exit")
            l_switch_cmd.append("d chg ING_DVP_TABLE;exit")

            l_switch_cmd.append("d chg ING_DVP_TABLE;exit")
            l_switch_cmd.append("d chg ING_EN_EFILTER_BITMAP;exit")
            l_switch_cmd.append("d chg ING_L3_NEXT_HOP;exit")
            l_switch_cmd.append("d chg ING_VLAN_VFI_MEMBERSHIP;exit")
            l_switch_cmd.append("d chg INITIAL_ING_L3_NEXT_HOP;exit")
            l_switch_cmd.append("d chg ING_VLAN_VFI_MEMBERSHIP;exit")
            l_switch_cmd.append("d chg L2MC;exit")
            l_switch_cmd.append("d chg L3_IPMC;exit")

            l_switch_cmd.append("d chg VFI_PROFILE;exit")
            l_switch_cmd.append("d chg EGR_DVP_ATTRIBUTE;exit")
            l_switch_cmd.append("d chg EGR_IPMC;exit")
            l_switch_cmd.append("d chg EGR_L3_NEXT_HOP;exit")
            l_switch_cmd.append("d chg EGR_VFI;exit")
            l_switch_cmd.append("d chg EGR_VLAN_VFI_MEMBERSHIP;exit")
            l_switch_cmd.append("d chg EGR_MAC_ADDRESS_PROFILE;exit")
            l_switch_cmd.append("d chg EGR_L3_INTF;exit")

            l_switch_cmd.append("d chg L3_DEFIP;exit")
            l_switch_cmd.append("d chg L3_IIF_PROFILE;exit")
            l_switch_cmd.append("d chg L3_IIF_ATTRS_2;exit")
            l_switch_cmd.append("d chg SVP_ATTRS_2;exit")
            l_switch_cmd.append("d chg MY_STATION_PROFILE_1;exit")
            l_switch_cmd.append("d chg MY_STATION_TCAM;exit")
            l_switch_cmd.append("d chg EGR_MAC_ADDRESS_PROFILE;exit")
            l_switch_cmd.append("d chg L3_ENTRY_SINGLE;exit")
            l_switch_cmd.append("d chg UNKNOWN_UCAST_BLOCK_MASK;exit")
            l_switch_cmd.append("d chg UNKNOWN_UCAST_BLOCK_MASK;exit")

            for switch_cmd in l_switch_cmd:
                for ipadd in ipadd_list:                
                    try:
                        out=''
                        child = pexpect.spawn('ssh %s@%s'%(switch_user, ipadd))
                        i = child.expect([pexpect.TIMEOUT, 'yes/no', '->', '(?i)password'])
                        if i == 0: # Timeout
                            print('ERROR! could not login with SSH')
                            print(child.before, child.after)
                            print(str(child))
                            sys.exit (1)
                        if i == 1:
                            child.sendline ('yes')
                            child.expect ('(?i)password')
                            child.sendline(switch_password)
                        if i == 2:
                            pass
                        if i == 3:
                            child.sendline(switch_password)
                        out+=cmd(child, 'su', '->', 5)
                        out+=cmd(child, 'bshell', '', 10)
                        out+=cmd(child, switch_cmd, '', 20)                   
                        entry_log(out,"BSHELL",ipadd)           
                    except Exception as error:
                        print(error)
                    pass

            for ipaddress in ipadd_list:
                function = "CLI" 
                logfilename = strftime('%Y-%m-%d', localtime(time())) + "_lastlog_saa_{0}_{1}.log".format(function,ipaddress)
                print(logfilename)
                logfilepath = "/var/log/devices/{0}".format(logfilename)
                if os.path.exists(logfilepath) == False:
                    info = ("Service Assurance Agent - OmniSwitch {0} is unreachable for log collection of CLI command output").format(ipaddress)
                    send_message(info,jid)                    
                    continue
 
                subject = ("Service Assurance Agent - SAA probe {0} configured on OmniSwitch {1} / {2} failed").format(saa_name,ipadd,host)
                result = ("We have collected the CLI and BSHELL logs of the following OmniSwitches: {0}").format(ipadd_list)
                action = "Find enclosed to this notification the log collection"
                category = "saa_{0}_{1}".format(ipaddress,function)
                send_file(logfilepath, subject, action, result, category)

            for ipaddress in ipadd_list:
                function = "BSHELL" 
                logfilename = strftime('%Y-%m-%d', localtime(time())) + "_lastlog_saa_{0}_{1}.log".format(function,ipaddress)
                print(logfilename)
                logfilepath = "/var/log/devices/{0}".format(logfilename)
                if os.path.exists(logfilepath) == False:
                    info = ("Service Assurance Agent - OmniSwitch {0} is unreachable for log collection of BSHELL command output").format(ipaddress)
                    send_message(info,jid)   
                    continue

                subject = ("Service Assurance Agent - SAA probe {0} configured on OmniSwitch {1} / {2} failed").format(saa_name,ipadd,host)
                result = ("We have collected the CLI and BSHELL logs of the following OmniSwitches: {0}").format(ipadd_list)
                action = "Find enclosed to this notification the log collection"
                category = "saa_{0}_{1}".format(ipaddress,function)
                send_file(logfilepath, subject, action, result, category)

            try:
                filename= '{0}_pmonitor_saa.enc'.format(host)
                remoteFilePath = '/flash/pmonitor.enc'
                localFilePath = "/tftpboot/{0}_{1}-{2}_{3}_{4}".format(date,date_hm.hour,date_hm.minute,ip,filename)
                get_file_sftp(switch_user, switch_password, ip, remoteFilePath, localFilePath)
                info = "Service Assurance Agent - Port Monitoring capture - download success"
                send_message(info,jid)               
            except:
                info = "Service Assurance Agent - Port Monitoring capture - download failed"
                send_message(info,jid)
                pass
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ipadd, "SAA Name": saa_name}, "fields": {"count": 1}}])
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