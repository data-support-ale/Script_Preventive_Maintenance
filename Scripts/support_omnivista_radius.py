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

    def get( self, path ):
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



def restart_freeradius_service():
       ssh = createSSHClient(ip, "2222", User_root, Password_root)

       cmd = "stop freeradius service"
       stdin, out, err = ssh.exec_command(cmd)
       out.read()

       cmd = "start freeradius service"
       stdin, out, err = ssh.exec_command(cmd)
       out.read()

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
      try:
        write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {"IP": ip, "Total": value}, "fields": {"count": 1}}])
        sys.exit()   
      except UnboundLocalError as error:
         print(error)
         sys.exit()
      except Exception as error:
        print(error)
        sys.exit() 

   elif save_resp == "1":
      answer = '2'
   else:
      answer = '1'

   if answer == '1':
        os.system('logger -t montag -p user.info Process terminated')
        restart_freeradius_service()
        sleep(2)
        logfilename = strftime('%Y-%m-%d', localtime(time())) + "_lastlog_radius_check.log"
        logfilepath = "/opt/ALE_Script/{0}".format(logfilename)
        category = "radius_issue"
        subject = "The number of devices authenticated on Radius Server {0} was below defined threshold.".format(ip)
        action = "Action done: the Radius services are restarted and we keep monitoring the number of authentications"
        result = "Find enclosed to this notification the log collection"
        send_file(logfilepath, subject, action, result, category)

   elif answer == '2':
        os.system('logger -t montag -p user.info Process terminated')
        restart_freeradius_service()
        sleep(2)

while True:
   try:
      main()
   except Exception as e:
      info = "Error when collecting Radius data : {0} ".format(e)
      send_message(info, jid)   
      entry_log(info)
   sleep(900)