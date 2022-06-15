#!/usr/local/bin/python3.7

import requests, json
import os
import datetime
import sys
import re
import configparser
from support_send_notification import send_message, send_message_request
from support_tools_OmniSwitch import check_save, add_new_save, send_file
from time import gmtime, strftime, localtime, sleep, time
import paramiko
from database_conf import *




#------------------------------------------------------------------------------

threshold_total = 0
threshold_guest=0
threshold_byod=0
threshold_employee=0
threshold_unknown=0
mails = list()
jid=""
nb_item_conf = 0
nb_item_notif = 0
email_notif=0
jid_notif=0
struct_conf = "\n\n[Information]\nIP/URL=192.168.1.1\nLogin=admin\nPassword=switch\n\n[Threshold]\nThresold_All=100\nThresold_Guest=0\nThresold_BYOD=30\nThresold_Employee=50\nThresold_Unknown=0\n\n[Mail]\nReceiver_Mail_Addresses=receiver1@notification.fr,receiver2@notification.com\nSender_Mail_Address=sender@notification.com\nMail_Password=senderpass\nMail_Server=smtp.notification.com\nPort_Mail_Server=465\n\n[Rainbow]\nRainbow_Jid=xxxxxxxxxxxx@openrainbow.com"

def entry_log(log):
  """ 
  This function permit the collection of script logs
  :param str old_log:           The entire log string
  :param str portnumber:        The new entry in logs string
  :return:                      None

  """
  logfilename = strftime('%Y-%m-%d', localtime(time())) + "_lastlog_radius_check.log"
  logfilepath = "/var/log/devices/{0}".format(logfilename)
  #path = os.getcwd()
  print(log)
  with open(logfilepath, "a") as file:
     file.write("{0}: {1}\n".format(datetime.datetime.now(),log))

path = os.getcwd() #get the full path of the  working directory
cp = configparser.ConfigParser()
try:
   configfile = '/opt/ALE_Script/OV_radius_checker.conf'
except:
  info = "Error when openning config file; Check the name OV_radius_checker.conf and retry.\n If the script has been executed by command lines, be sure to be in the same directory as the executable."
  entry_log(info)
  sys.exit()
try:
  cp.read(configfile)
except:
   info ="Error when openning config file; Check the conf file structure and retry.\nCompare with the file structure : {0} ".format(struct_conf)
   entry_log(info)
   sys.exit()


try:
   User = cp.get('Information', 'Login')
   Pass = cp.get('Information', 'Password')
   User_root = "root"
   Password_root = "223405d70e8e5c31a0f28d0517556581a0adeb7d"

   ip = cp.get('Information', 'IP/URL')
except:
   info = "Error when collecting credentials information in conf file.(One element or more is missing.)\nCompare with the file structure : {0}".format(struct_conf)
   entry_log(info)
   sys.exit()

if User == "" or Pass == "" or ip == "":
   info = "Error when collecting credentials information in conf file.(One element or more is empty.)"
   entry_log(info)
   sys.exit()


try:
   threshold_total = cp.get('Threshold', 'Threshold_All')
   threshold_guest = cp.get('Threshold', 'Threshold_Guest')
   threshold_byod = cp.get('Threshold', 'Threshold_BYOD')
   threshold_employee = cp.get('Threshold', 'Threshold_Employee')
   threshold_unknown = cp.get('Threshold', 'Threshold_Unknown')
except:
   info = "Error when collecting threshold information in conf file.(One element or more is missing.)\nCompare with the file structure : {0}".format(struct_conf)
   entry_log(info)
   sys.exit()
if  threshold_total == "" or threshold_guest == "" or threshold_byod == "" or threshold_employee == "" or threshold_unknown == "" :
   info = "Error when collecting threshold information in conf file.(One element or more is empty.)"
   entry_log(info)
   sys.exit()

if  not (threshold_total.isnumeric()  and threshold_guest.isnumeric()  and threshold_byod.isnumeric() and threshold_employee.isnumeric() and threshold_unknown .isnumeric()):
   info = "Error when collecting threshold information in conf file.(One element or more is not an integer.)"
   entry_log(info)
   sys.exit()


try:
   mail_tmp = cp.get('Mail', 'Receiver_Mail_Addresses').replace(";",",").split(",")
   for mail in mail_tmp:
      if re.search("(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)",mail):
         mails.append(mail)

   mail_user = cp.get('Mail', 'Sender_Mail_Address')
   mail_password = cp.get('Mail', 'Mail_Password')
   mail_server = cp.get('Mail', 'Mail_Server')
   port_server = cp.get('Mail', 'Port_Mail_Server')
except:
   info = "Error when collecting email information in conf file.(One element or more is missing.)\nCompare with the file structure : {0}".format(struct_conf)
   entry_log(info) 
   sys.exit()

if len(mails)==0 or mail_tmp == "" or mail_user == "" or mail_password == "" or mail_server == "" or port_server == "" :
   info = "Error when collecting rainbow information in conf file.(One element or more is empty.)"
   entry_log(info)

   info = "Email not configured"
   entry_log(info)
   email_notif=0
else:
  email_notif=1
  if not re.search("(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)",mail_user):
     info = "Sender email address {0} does not comply, Email not configured. ".format(mail_user)
     entry_log(info) 
     email_notif=0
  if not port_server.isnumeric():
     info = "Server port number : {0} is not a number, Email not configured. ".format(port_server)
     entry_log(info)
     email_notif=0
try:
   jid = cp.get('Rainbow', 'Rainbow_Jid')
except:
   info = "Error when collecting rainbow information in conf file.(the element is missing.)\nCompare with the file structure : {0}".format(struct_conf)
   entry_log(info)
   sys.exit()
if jid =='':
   info = "Rainbow not configured"
   entry_log(info)
   jid_notif=0
else:
  if re.search("^.*@openrainbow.com$",jid):
    jid_notif=1
  else: 
     info = "The Rainbow JID doesn't correspond with what was expected, Rainbow not configured"
     entry_log(info)
     jid_notif=0
  

if jid_notif==0 and email_notif==0:
  info = "Please enter at least one type of notification"
  entry_log(info)
  sys.exit()

def createSSHClient(server, port, user, password):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client


class OvHandler:

    def __init__(self):
        url = "https://"+ ip + ":443/api/"
        self.ov = url
        self.cookies = dict()
       # print(self.cookies)
        if not 'accessToken' in self.cookies:
           login = self.post( 'login', { 'userName': User, 'password': Pass } )
           self.cookies['accessToken'] = login['accessToken']


    def post( self, path, obj ):
         fullpath = self.ov + path
         info = "In post path %s"%fullpath
         entry_log(info)

         r = requests.post( fullpath, json.dumps( obj ),
                           cookies=self.cookies,
                           verify=False,
                           headers={ 'content-type': 'application/json' } )
         try:
            info = "The post server response : \n {0} \n ".format(r.text)
            entry_log(info)
            return json.loads( r.text )
         except requests.exceptions.ConnectionError as response:
            print(response)
            try:
                  write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                     "HTTP_Request": fullpath, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                  print(error)
                  sys.exit()
            except Exception as error:
                  print(error)
                  pass
         except requests.exceptions.Timeout as response:
            print("Request Timeout when calling URL: " + fullpath)
            print(response)
            try:
                  write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                     "HTTP_Request": fullpath, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                  print(error)
                  sys.exit()
            except Exception as error:
                  print(error)
                  pass
         except requests.exceptions.TooManyRedirects as response:
            print("Too Many Redirects when calling URL: " + fullpath)
            print(response)
            try:
                  write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                     "HTTP_Request": fullpath, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                  print(error)
                  sys.exit()
            except Exception as error:
                  print(error)
                  pass
         except requests.exceptions.RequestException as response:
            print("Request exception when calling URL: " + fullpath)
            print(response)
            try:
                  write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                     "HTTP_Request": fullpath, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                  print(error)
                  sys.exit()
            except Exception as error:
                  print(error)
                  pass

    def get( self, path ):
         fullpath = self.ov + path
         r = requests.get( self.ov + path,
                          cookies=self.cookies,
                          verify=False,
                          headers={ 'content-type': 'application/json' } )

         try:
            info = "The get server response : \n {0} \n ".format(r.text)
            entry_log(info)
            return json.loads( r.text )
         except requests.exceptions.ConnectionError as response:
            print(response)
            try:
                  write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                     "HTTP_Request": fullpath, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                  print(error)
                  sys.exit()
            except Exception as error:
                  print(error)
                  pass
         except requests.exceptions.Timeout as response:
            print("Request Timeout when calling URL: " + fullpath)
            print(response)
            try:
                  write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                     "HTTP_Request": fullpath, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                  print(error)
                  sys.exit()
            except Exception as error:
                  print(error)
                  pass
         except requests.exceptions.TooManyRedirects as response:
            print("Too Many Redirects when calling URL: " + fullpath)
            print(response)
            try:
                  write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                     "HTTP_Request": fullpath, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                  print(error)
                  sys.exit()
            except Exception as error:
                  print(error)
                  pass
         except requests.exceptions.RequestException as response:
            print("Request exception when calling URL: " + fullpath)
            print(response)
            try:
                  write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {
                     "HTTP_Request": fullpath, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                  print(error)
                  sys.exit()
            except Exception as error:
                  print(error)
                  pass

    
    def postRadiusDeviceNumber(self):

        value_guest=0
        value_byod=0
        value_employee=0
        value_unknown=0
        r=self.post('ham/summary/onlinedevicenumber',{ 'timespan':'104', 'authType': ['Framed-User']})

        python_obj = json.loads( json.dumps(r, sort_keys=True, indent=4, separators=(',', ': ')))
      # print (json.dumps(r, sort_keys=True, indent=4, separators=(',', ': ')))
        for type in python_obj["data"]:
           if type["lineName"] == "Guest":
              guest = type["lineData"]
              last_value_guest= guest[-1]
              value_guest=last_value_guest["value"]

           if type["lineName"] == "BYOD":
              byod = type["lineData"]
              last_value_byod= byod[-1]
              value_byod=last_value_byod["value"]

           if type["lineName"] == "Employee":
              employee = type["lineData"]
              last_value_employee= employee[-1]
              value_employee=last_value_employee["value"]

           if type["lineName"] == "Unknown":
              unknown = type["lineData"]
              last_value_unknown= unknown[-1]
              value_unknown=last_value_unknown["value"]

        value_total = int(value_guest)+ int(value_byod)+ int(value_employee)+ int(value_unknown)
        print()
        info = "The number of Guest Alive Radius authentification is {0}".format(value_guest)
        entry_log(info)
        print()
        info = "The number of BYOD Alive Radius authentification is {0}".format(value_byod)
        entry_log(info)
        print()
        info = "The number of Employee Alive Radius authentification is {0}".format(value_employee)
        entry_log(info)
        print()
        info = " The number of Unknown Alive Radius authentification is {0}".format(value_unknown)
        entry_log(info)
        print()
        info =  "The Total number of Alive Radius authentification is {0}".format(value_total)
        entry_log(info)
        print()
        return value_total, int(value_guest), int(value_byod), int(value_employee), int(value_unknown)

# Function SSH for checking connectivity before collecting logs
def ssh_connectivity_check(User_root, Password_root, ipadd, cmd):
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
        p.connect(ipadd, port=2222, username=User_root,password=Password_root, timeout=20.0, banner_timeout=200)
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

def restart_freeradius_service():
       #ssh = createSSHClient(ip, "2222", User_root, Password_root)
       text = "More logs about the switch : {0} \n\n\n".format(ip)
       cmd = "systemctl stop ovupam; systemctl stop ovradius; sleep 2; systemctl start ovupam; systemctl start ovradius"
       #cmd = "sleep 2"
       output = ssh_connectivity_check(User_root, Password_root, ip, cmd)
       if output != None:
               output = str(output)
               output_decode = bytes(output, "utf-8").decode("unicode_escape")
               output_decode = output_decode.replace("', '","")
               output_decode = output_decode.replace("']","")
               output_decode = output_decode.replace("['","")
               text = "{0}{1}: \n{2}\n\n".format(text, cmd, output_decode)
       else:
               exception = "Timeout"
               info = ("Timeout when establishing SSH Session to OmniSwitch {0}, we cannot collect logs").format(ip)
               print(info)
               os.system('logger -t montag -p user.info ' + info)
               send_message(info, jid)
               try:
                  write_api.write(bucket, org, [{"measurement": "support_ssh_exception", "tags": {"Reason": "CommandExecution", "IP_Address": ip, "Exception": exception}, "fields": {"count": 1}}])
               except UnboundLocalError as error:
                  print(error)
               except Exception as error:
                  print(error)
                  pass 
               sys.exit()

def main():
   # Create OV REST Session
   ovrest = OvHandler()
   info = "----Test Python Script"
   entry_log(info)

   value_total, value_guest, value_byod,value_employee, value_unknown = ovrest.postRadiusDeviceNumber()
   user_type = "0" 

   try:
      write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ip, "Total": value_total, "Guest": value_guest, "BYOD": value_byod, "Employee": value_employee, "Unknown": value_unknown}, "fields": {"count": 1}}]) 
   except UnboundLocalError as error:
      print(error)
      sys.exit()
   except Exception as error:
      print(error)
      sys.exit()     
    
   if value_total < int(threshold_total):
      info= "The Total number of Devices authenticated over the Radius Server is  {0} under the fixed Threshold : {1}. Do you want to restart the Radius services?".format(value_total,threshold_total)
      subject = "Number of Total Active Radius Authentication is under than fixed Threshold, Radius service has been restarted"
      threshold = threshold_total
      value = value_total
      entry_log(info)
      user_type="Devices"
      rainbow_notif(user_type, value_total, threshold)
      #restart_freeradius_service()
      #entry_log(info)
      #send_message_request(info,jid)

   elif value_employee < int(threshold_employee):
      info="The Total number of Users authenticated over the Radius Server is  {0} under the fixed Threshold : {1}. Do you want to restart the Radius services?".format(value_employee,threshold_employee)
      subject = "Number of Employee Active Radius Authentication is under than fixed Threshold, Radius service has been restarted"
      threshold = threshold_employee
      value = value_employee
      entry_log(info)
      user_type="Users"
      rainbow_notif(user_type, value_total, threshold)
       #restart_freeradius_service()
       #entry_log(info)
       #send_message_request(info,jid)

   elif value_byod < int(threshold_byod):
      info="The Total number of BYOD Users authenticated over the Radius Server is  {0} under the fixed Threshold : {1}. Do you want to restart the Radius services?".format(value_byod,threshold_byod)
      subject = "Number of BYOD Active Radius Authentication is under than fixed Threshold, Radius service has been restarted"
      entry_log(info)
      threshold = threshold_byod
      value = value_byod
      user_type="BYOD Users"
      rainbow_notif(user_type, value_total, threshold)
       #restart_freeradius_service()
       #entry_log(info)
       #send_message_request(info,jid)

   elif value_guest < int(threshold_guest):
      info="The Total number of Guest Users authenticated over the Radius Server is  {0} under the fixed Threshold : {1}. Do you want to restart the Radius services?".format(value_guest,threshold_guest)
      subject = "Number of Guest Active Radius Authentication is under than fixed Threshold, Radius service has been restarted"
      entry_log(info)
      threshold = threshold_guest
      value = value_guest
      user_type="Guest Users"
      rainbow_notif(user_type, value_total, threshold)
       #restart_freeradius_service()
       #entry_log(info)
       #send_message_request(info,jid)

   elif value_unknown < int(threshold_unknown):
      info="The Total number of Unknown Devices authenticated over the Radius Server is  {0} under the fixed Threshold : {1}. Do you want to restart the Radius services?".format(value_unknown,threshold_unknown)
      subject = "Number of Unknown Active Radius Authentication is under than fixed Threshold, Radius service has been restarted"
      entry_log(info)
      threshold = threshold_unknown
      value = value_unknown
      user_type="Unknown Devices"
      rainbow_notif(user_type, value_total, threshold)
       #restart_freeradius_service()
       #entry_log(info)
       #send_message_request(info,jid)

def rainbow_notif(user_type, value, threshold):
   save_resp = check_save(user_type, ip, "radius")

   if save_resp == "0":
      notif = "The Total number of {0} authenticated over the Radius Server is  {1} under the fixed Threshold : {2}. Do you want to restart the Radius services?".format(user_type,value,threshold)

      answer = send_message_request(notif, jid)
      print(answer)
      if answer == "2":
         add_new_save(user_type, ip, "radius", choice="always")
      elif answer == "0":
         add_new_save(user_type, ip, "radius", choice="never")

   elif save_resp == "-1":
      answer = "0"

   elif save_resp == "1":
      answer = '2'
   else:
      answer = '1'

   if answer == '1':
        os.system('logger -t montag -p user.info Received Answer Yes')
        restart_freeradius_service()
        sleep(2)
        logfilename = strftime('%Y-%m-%d', localtime(time())) + "_lastlog_radius_check.log"
        logfilepath = "/var/log/devices/{0}".format(logfilename)
        category = "radius_issue"
        subject = "The number of devices authenticated on Radius Server {0} was below defined threshold.".format(ip)
        action = "Action done: the Radius services are restarted and we keep monitoring the number of authentications"
        result = "Find enclosed to this notification the log collection"
        send_file(logfilepath, subject, action, result, category, jid)

   elif answer == '2':
        os.system('logger -t montag -p user.info Received Answer Yes and Remember')
        restart_freeradius_service()
        sleep(2)
   else:
      pass

while True:
   try:
      main()
   except Exception as e:
      info = "Error when collecting Radius data : {0} ".format(e)
      send_message(info, jid)   
      entry_log(info)
   sleep(900)