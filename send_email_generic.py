#!/usr/bin/env python

import sys
import os
import getopt
import json
import logging
import subprocess
from time import gmtime, strftime, localtime, sleep
import requests
import datetime
import smtplib
import mimetypes
import re
from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from support_tools import get_credentials
from support_send_notification import send_message,send_file,send_alert
from support_OV_get_wlan import OvHandler
from database_conf import *

script_name = sys.argv[0]
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

uname = os.system('uname -a')
os.system('logger -t montag -p user.info Executing script ' + script_name)
system_name = os.uname()[1].replace(" ", "_")

#Init Timestamp in second
timestamp = 300
timestamp = (timestamp/60)*100

def deassociation(ipadd,device_mac,timestamp,reason,reason_number):
  message = "WLAN Deassociation detected reason : {0} from Stellar AP {1}, client MAC Address {2}".format(reason,ipadd,device_mac)
  message_bis = "WLAN Deassociation detected reason : {0} from Stellar AP {1}".format(reason_number,ipadd)
  os.system('logger -t montag -p user.info ' + message_bis)
  subject_content="[TS LAB] A deassociation is detected on Stellar AP!"
  message_content_1= "WLAN Alert - There is a WLAN deassociation detected on server {0} from Stellar AP {1}, Device's MAC Address: {2} .".format(system_name,ipadd,device_mac)
  print(message_content_1)
  message_content_2="Reason number: ".format(reason_number)
  send_alert(message,jid)
  send_message(message_reason,jid)
  
  write_api.write(bucket, org, [{"measurement": "support_wlan_deassociation", "tags": {"AP_IPAddr": ipadd, "Client_MAC": device_mac, "Reason_Deassociation": reason}, "fields": {"count": 1}}])

  #send_mail(timestamp,subject_content,message_content_1,message_content_2,ipadd)
  ## REST-API for login on OV
  ovrest = OvHandler()
  ## REST-API for getting WLAN information from OV Wireless List
  channel, clientName = ovrest.postWLANClient(device_mac)
  category = ovrest.postWLANIoT(device_mac)
  ## If client does not exist on OV WLAN Client list
  if clientName != None:
     info =  "The client {0} MAC Address: {1} is associated to Radio Channel: {2}".format(clientName,device_mac,channel)
     send_message(info,jid)
  if category != None:
     info =  "This client device category is: {0}".format(category)
     send_message(info,jid)

def reboot(ipadd,timestamp):
  os.system('logger -t montag -p user.info reboot detected')
  subject_content="[TS LAB] A reboot is detected on Stellar AP!"
  message_content_1= "WLAN Alert - There is a Stellar reboot detected on server {0} from Stellar AP {1}".format(system_name,ipadd)
  message_content_2="sysreboot"
  send_alert(message_content_1,jid)
  send_message(message_reason,jid)

  write_api.write(bucket, org, [{"measurement": "support_wlan_ap_reboot", "tags": {"AP_IPAddr": ipadd, "Reason": "sysreboot"}, "fields": {"count": 1}}])

  send_mail(timestamp,subject_content,message_content_1,message_content_2,ipadd)

def upgrade(ipadd,timestamp):
  os.system('logger -t montag -p user.info upgrade detected')
  subject_content="[TS LAB] An upgrade is detected on Stellar AP!"
  message_content_1= "WLAN Alert - There is a Stellar upgrade detected on server {0} from Stellar AP {1}".format(system_name,ipadd)
  message_content_2="sysupgrade"
  send_alert(message_content_1,jid)
  send_message(message_reason,jid)

  write_api.write(bucket, org, [{"measurement": "support_wlan_ap_reboot", "tags": {"AP_IPAddr": ipadd, "Reason": "sysupgrade"}, "fields": {"count": 1}}])

  send_mail(timestamp,subject_content,message_content_1,message_content_2,ipadd)


def exception(ipadd,timestamp):
  os.system('logger -t montag -p user.info exception detected')
  subject_content="[TS LAB] An exception (Fatal exception, Exception stack, Kernel Panic) is detected on Stellar AP!"
  message_content_1= "WLAN Alert - There is a Stellar exception detected on server {0} from Stellar AP {1}".format(system_name,ipadd)
  message_content_2="Exception"
  send_alert(message_content_1,jid)
  send_message(message_reason,jid)

  write_api.write(bucket, org, [{"measurement": "support_wlan_ap_reboot", "tags": {"AP_IPAddr": ipadd, "Reason": "exception"}, "fields": {"count": 1}}])

  send_mail(timestamp,subject_content,message_content_1,message_content_2,ipadd)

def internal_error(ipadd,timestamp):
  os.system('logger -t montag -p user.info internal error detected')
  subject_content="[TS LAB] An Internal Error is detected on Stellar AP!"
  message_content_1= "WLAN Alert - There is an Internal Error detected on server {0} from Stellar AP {1}".format(system_name,ipadd)
  message_content_2="Internal Error"
  send_alert(message_content_1,jid)
  send_message(message_reason,jid)

  write_api.write(bucket, org, [{"measurement": "support_wlan_ap_reboot", "tags": {"AP_IPAddr": ipadd, "Reason": "internal error"}, "fields": {"count": 1}}])

  send_mail(timestamp,subject_content,message_content_1,message_content_2,ipadd)

def target_asserted(ipadd,timestamp):
  os.system('logger -t montag -p user.info target asserted detected')
  subject_content="[TS LAB] A Target Asserted Error is detected on Stellar AP!"
  message_content_1= "WLAN Alert - There is a Target Asserted error detected on server {0} from Stellar AP {1}".format(system_name,ipadd)
  message_content_2="Target Asserted"
  send_alert(message_content_1,jid)
  send_message(message_reason,jid)

  write_api.write(bucket, org, [{"measurement": "support_wlan_ap_reboot", "tags": {"AP_IPAddr": ipadd, "Reason": "target asserted"}, "fields": {"count": 1}}])

  send_mail(timestamp,subject_content,message_content_1,message_content_2,ipadd)

def kernel_panic(ipadd,timestamp):
  os.system('logger -t montag -p user.info Kernel Panic detected')
  subject_content="[TS LAB] A Kernel Panic is detected on Stellar AP!"
  message_content_1= "WLAN Alert - There is a Kernel Panic error detected on server {0} from Stellar AP {1}".format(system_name,ipadd)
  message_content_2="Kernel panic"
  send_alert(message_content_1,jid)
  send_message(message_reason,jid)

  write_api.write(bucket, org, [{"measurement": "support_wlan_ap_reboot", "tags": {"AP_IPAddr": ipadd, "Reason": "kernel panic"}, "fields": {"count": 1}}])

  send_mail(timestamp,subject_content,message_content_1,message_content_2,ipadd)

def limit_reached(ipadd,timestamp):
  os.system('logger -t montag -p user.info Associated STA Limit Reached!')
  subject_content="[TS LAB] Associated STA Limit Reached!"
  message_content_1= "WLAN Alert - The Stellar AP {0} has reached the limit of WLAN Client association!".format(ipadd)
  message_content_2="Associated STA limit reached"
  send_alert(message_content_1,jid)
  send_message(message_reason,jid)

  write_api.write(bucket, org, [{"measurement": "support_wlan_ap_reboot", "tags": {"AP_IPAddr": ipadd, "Reason": "STA limit reached"}, "fields": {"count": 1}}])

  send_mail(timestamp,subject_content,message_content_1,message_content_2,ipadd)

def send_mail(timestamp,subject_content,message_content_1,message_content_2,ipadd):
  myDate = datetime.date.today()

  path_log_attachment = "/var/log/devices/{0}/syslog.log".format(ipadd)
  json_file = "/var/log/devices/lastlog_deauth.json".format(ipadd,myDate.isoformat())

  content_variable = open (path_log_attachment,'r')
  file_lines = content_variable.readlines()
  content_variable.close()

  logs_saved = list()

  last_line = file_lines[-1].split(',')
  last_time = last_line[0]
  last_time_split = last_time[-len(last_time)+26:-7].split(':')
  #time in hour into decimal of the last time : #else there is en error due to second  changes 60 to 0
  hour = last_time_split[0]
  #"%02d" %  force writing on 2 digits
  minute_deci = "%02d" % int(float(last_time_split[1])*100/60)
  second_deci = "%02d" % int(float(last_time_split[2])*100/60)
  last_time = "{0}{1}{2}".format(hour,minute_deci,second_deci)

  #We start from the last line
  for line in reversed(file_lines):

       current_line = line.split(',')
       current_time = current_line[0]
       #time in hour into decimal of the last time : #else there is en error due to second  changes 60 to 0
       current_time_split = current_time[-len(current_time)+26:-7].split(':')
       hour = current_time_split[0]
       #"%02d" %  force writing on 2 digits
       minute_deci = "%02d" % int(float(current_time_split[1])*100/60)
       second_deci = "%02d" % int(float(current_time_split[2])*100/60)
       current_time = "{0}{1}{2}".format(hour,minute_deci,second_deci)

       if (int(last_time)-int(current_time)) > timestamp:
          break

       for element in current_line:
         if sys.argv[1] == "deauth":
          if re.search(device_mac,element):
             logs_saved.append(line)
         elif sys.argv[1] == "reboot" or sys.argv[1] == "exception" or sys.argv[1] == "internal_error" or sys.argv[1] == "target_asserted":
           if re.search(ipadd,element):
              logs_saved.append(line)
         else:
           break

  attachment = reversed(logs_saved)
  f_attachment = open('/var/log/devices/deauth_attachement.log','w')
  f_attachment.write("".join(attachment))
  f_attachment.close()

  fp = open('/var/log/devices/deauth_attachement.log','r')

  part3 = MIMEBase('application', "octet-stream")
  part3.set_payload((fp).read())
  fp.close()
  encoders.encode_base64(part3)
  part3.add_header('Content-Disposition', "attachment; filename= %s" % os.path.basename("/var/log/devices/{0}_{1}_history.log".format(ipadd,myDate.isoformat())))

  for mail in mails:
   sent_from = gmail_user
   to = mail

   ### Adding MIME support
   message = MIMEMultipart("alternative")
   message["Subject"] = "{0}".format(subject_content)
   message["From"] = sent_from
   message["To"] = to

   email_text = """\
   Subject: {0}
   Hello
   {1}
    Reason Number: {2}
    Message: {3}""".format(subject_content,message_content_1,message_content_2,message_reason)


   email_html = """\
   <html>
     <body>
       <p>
       <br>   Hello </br>
          {0}
       </p>
           <br>   Reason number: {1} </br>
       </p>
           <br>  {2}                 </br>
<table class=Tabellanormale border=0 cellpadding=0 align=left width=100 style='width:75.0pt'><tr><td style='border:none;border-top:solid #6B489D 4.5pt;padding:.75pt .75pt .75pt .75pt'></td></tr></table><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 width="100%" style='width:100.0%;background:white'><tr><td valign=top style='padding:0cm 0cm 0cm 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 width="100%" style='width:100.0%'><tr><td valign=top style='padding:11.25pt 0cm 11.25pt 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 width="100%" style='width:100.0%'><tr><td valign=top style='padding:0cm 0cm 0cm 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 width="100%" style='width:100.0%'><tr><td valign=top style='padding:0cm 0cm 0cm 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 align=left width=420 style='width:315.0pt'><tr><td valign=top style='padding:0cm 0cm 0cm 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 align=left><tr><td style='padding:0cm 0cm 0cm 0cm'><p class=MsoNormal><b><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#6B489D'>NBD Support Team<o:p></o:p></span></b></p></td></tr><tr><td style='padding:0cm 0cm 7.5pt 0cm'><p class=MsoNormal style='line-height:13.5pt'><span style='font-size:10.0pt;font-family:ClanOT-Book;color:black'>Alcatel-Lucent Enterprise <o:p></o:p></span></p></td></tr><tr><td style='padding:0cm 0cm 7.5pt 0cm'><p class=MsoNormal><span style='font-size:10.0pt;font-family:ClanOT-Book;color:black'><o:p></o:p></span></p><p class=MsoNormal><span style='font-size:10.0pt;font-family:ClanOT-Book;color:black'><o:p>&nbsp;</o:p></span></p><p class=MsoNormal><b><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#6B489D'><a href="https://web.openrainbow.com/" target="_blank"><span style='color:#6B489D;border:none windowtext 1.0pt;padding:0cm'>Rainbow collaboration platform</span><span style='color:#6B489D;border:none windowtext 1.0pt;padding:0cm;font-weight:normal'> </span></a><o:p></o:p></span></b></p></td></tr><tr><td style='padding:0cm 0cm 0cm 0cm'><p class=MsoNormal style='line-height:13.5pt'><span style='font-size:10.0pt;font-family:ClanOT-Book;color:black'>ALE International <o:p></o:p></span></p></td></tr><tr><td style='padding:0cm 0cm 0cm 0cm'><p class=MsoNormal style='line-height:13.5pt'><span lang=FR style='font-size:10.0pt;font-family:ClanOT-Book;color:black'>115-225 rue A. de St-Exupery<o:p></o:p></span></p><p class=MsoNormal style='line-height:13.5pt'><span lang=FR style='font-size:10.0pt;font-family:ClanOT-Book;color:black'>ZAC Prat Pip - Guipavas<o:p></o:p></span></p></td></tr><tr style='height:60.9pt'><td style='padding:0cm 0cm 7.5pt 0cm;height:60.9pt'><p class=MsoNormal style='line-height:13.5pt'><span style='font-size:10.0pt;font-family:ClanOT-Book;color:black'>29806 BREST, France</span><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#3A3A3A'> <o:p></o:p></span></p><p class=MsoNormal style='line-height:13.5pt'><span style='font-size:10.0pt'><a href="https://www.al-enterprise.com/"><span style='font-family:ClanOT-Book;color:#3A3A3A;text-decoration:none'><img border=0 width=173 height=76 style='width:1.802in;height:.7916in' id="Picture_x0020_1" src="cid:image009.png@01D72707.92BFB2D0" alt="https://www.al-enterprise.com/-/media/assets/internet/images/h-to-m/logo-389x170.png"></span></a></span><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#3A3A3A'><o:p></o:p></span></p><p class=MsoNormal style='line-height:13.5pt'><span style='font-size:10.0pt'><a href="https://www.linkedin.com/company/alcatellucententerprise/"><span style='font-family:ClanOT-Book;color:#3A3A3A;text-decoration:none'><img border=0 width=30 height=30 style='width:.3125in;height:.3125in' id="Picture_x0020_39" src="cid:image010.png@01D72707.92BFB2D0" alt="https://www.al-enterprise.com/-/media/assets/internet/images/h-to-m/in-1080x1080.png"></span></a></span><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#3A3A3A'> </span><span style='font-size:10.0pt'><a href="https://twitter.com/ALUEnterprise"><span style='font-family:ClanOT-Book;color:#3A3A3A;text-decoration:none'><img border=0 width=30 height=30 style='width:.3125in;height:.3125in' id="Picture_x0020_40" src="cid:image011.png@01D72707.92BFB2D0" alt="https://www.al-enterprise.com/-/media/assets/internet/images/t-to-z/tw-1080x1080.png"></span></a></span><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#3A3A3A'> </span><span style='font-size:10.0pt'><a href="https://www.facebook.com/ALUEnterprise"><span style='font-family:ClanOT-Book;color:#3A3A3A;text-decoration:none'><img border=0 width=30 height=30 style='width:.3125in;height:.3125in' id="Picture_x0020_41" src="cid:image012.png@01D72707.92BFB2D0" alt="https://www.al-enterprise.com/-/media/assets/internet/images/a-to-g/fb-1080x1080.png"></span></a></span><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#3A3A3A'><o:p></o:p></span></p></td></tr><tr><td style='padding:0cm 0cm 0cm 0cm'></td></tr></table></td></tr></table></td></tr></table></td></tr><tr><td valign=top style='padding:0cm 0cm 0cm 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 width="100%" style='width:100.0%'><tr><td valign=top style='padding:3.75pt 0cm 0cm 0cm'><p class=MsoNormal style='text-align:justify;text-justify:inter-ideograph;line-height:12.0pt'><span style='font-size:7.0pt;font-family:ClanOT-Book;color:#BBBCBC'>The Alcatel-Lucent name and logo are trademarks of Nokia used under license by ALE. <o:p></o:p></span></p><p class=MsoNormal style='text-align:justify;text-justify:inter-ideograph;line-height:12.0pt'><span style='font-size:7.0pt;font-family:ClanOT-Book;color:#BBBCBC'>This communication is intended to be received only by the individual or entity to whom or to which it is addressed and may contain information that is privileged, is confidential and is subject to copyright. Any unauthorized use, copying, review or disclosure of this communication is strictly prohibited. If you have received this communication in error, please delete this message from your email box and information system (including all files and documents attached) and notify the sender by reply email. Please consider protecting the environment before printing. Thank you for your cooperation.</span><span style='font-size:7.0pt;font-family:ClanOT-Book;color:#B8B8B8'> </span><span style='font-size:8.5pt;font-family:ClanOT-Book;color:#B8B8B8'><o:p></o:p></span></p></td></tr></table></td></tr></table></td></tr></table></td></tr></table><p class=MsoNormal><o:p>&nbsp;</o:p></p><p class=MsoNormal><o:p>&nbsp;</o:p></p></div>
     </body>
   </html>
   """.format(message_content_1,message_content_2,message_reason)

   # Turn these into plain/html MIMEText objects
   part1 = MIMEText(email_text, "plain")
   part2 = MIMEText(email_html, "html")

   # Add HTML/plain-text parts to MIMEMultipart message
   # The email client will try to render the last part first
   message.attach(part1)
   message.attach(part2)
   message.attach(part3)

   #email send request
   try:
       server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
       server.ehlo()
       server.login(gmail_user, gmail_password)
       server.sendmail(sent_from, to, message.as_string())
       server.close()

       print (runtime + 'Email sent!')
       logging.debug(runtime + 'Email sent!')
   except Exception as e:
       print(e)
       print ('Something went wrong...')

def extract_reason_new():
  last = ""
  reason = device_mac = ap_mac = 0
  with open("/var/log/devices/lastlog_deauth.json", "r") as log_file:
    for line in log_file:
        last = line

  with open("/var/log/devices/lastlog_deauth.json", "w") as log_file:
    log_file.write(last)

  with open("/var/log/devices/lastlog_deauth.json", "r") as log_file:
    log_json = json.load(log_file)
    msg =log_json["message"]
    f=msg.split(',')
    for element in f:
       if "reason" in element:
        reason = re.findall(r"reason (.*)", msg)[0]
        reason_number = re.findall(r"reason (.*?)\(", msg)[0]
        reason = str(reason)
        device_mac = re.findall(r".*\[(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\].*", msg)[0]
        ap_mac = re.findall(r".*\((([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\).*", msg)[0]
        device_mac = str(device_mac[0])
        ap_mac = str(ap_mac[0])
        print("WLAN Deauthentication use case")
        print(reason)
        print(device_mac)
        print(ap_mac)
  return reason,device_mac,reason_number;

def extract_ipadd():
   last = ""
   with open("/var/log/devices/lastlog_deauth.json", "r") as log_file:
    for line in log_file:
        last = line

   with open("/var/log/devices/lastlog_deauth.json", "w") as log_file:
    log_file.write(last)

   with open("/var/log/devices/lastlog_deauth.json", "r") as log_file:
    log_json = json.load(log_file)
    ipadd = log_json["relayip"]
    host = log_json["hostname"]
    message_reason = log_json["message"]
    ipadd = str(ipadd)
    print(ipadd)
    l = []
    l.append('/code ')
    l.append(message_reason)
    message_reason = ''.join(l)
   return ipadd,message_reason;

switch_user, switch_password, jid, gmail_user, gmail_password, mails,ip_server_log = get_credentials()
#print("Mail sent to: " + str(mails))

if sys.argv[1] == "deauth":
      print("call function deassociation")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      ipadd,message_reason = extract_ipadd()
      reason,device_mac,reason_number = extract_reason_new()
      deassociation(ipadd,device_mac,timestamp,reason,reason_number)
      os.system('logger -t montag -p user.info Sending email')
      os.system('logger -t montag -p user.info Process terminated')
      sys.exit(0)
elif sys.argv[1] == "roaming":
      print("WLAN Roaming - deauth reason 1")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      os.system('logger -t montag -p user.info Roaming occurs on Stellar AP ' + sys.argv[2])
elif sys.argv[1] == "leaving":
      print("WLAN Client disconnection")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      os.system('logger -t montag -p user.info Client is leaving SSID on Stellar AP ' + sys.argv[2])
elif sys.argv[1] == "reboot":
      print("call function reboot")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      ipadd,message_reason = extract_ipadd()
      reboot(ipadd,timestamp)
      os.system('logger -t montag -p user.info Sending email')
      os.system('logger -t montag -p user.info Process terminated')
      sys.exit(0)
elif sys.argv[1] == "upgrade":
      print("call function upgrade")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      ipadd,message_reason = extract_ipadd()
      upgrade(ipadd,timestamp)
      os.system('logger -t montag -p user.info Sending email')
      os.system('logger -t montag -p user.info Process terminated')
      sys.exit(0)
elif sys.argv[1] == "exception":
      print("call function exception")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      ipadd,message_reason = extract_ipadd()
      exception(ipadd,timestamp)
      os.system('logger -t montag -p user.info Sending email')
      os.system('logger -t montag -p user.info Process terminated')
      sys.exit(0)
elif sys.argv[1] == "target_asserted":
      print("call function target_asserted")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      ipadd,message_reason = extract_ipadd()
      target_asserted(ipadd,timestamp)
      os.system('logger -t montag -p user.info Sending email')
      os.system('logger -t montag -p user.info Process terminated')
      sys.exit(0)
elif sys.argv[1] == "internal_error":
      print("call function internal_error")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      ipadd,message_reason = extract_ipadd()
      internal_error(ipadd,timestamp)
      os.system('logger -t montag -p user.info Sending email')
      os.system('logger -t montag -p user.info Process terminated')
      sys.exit(0)
elif sys.argv[1] == "kernel_panic":
      print("call function kernel_panic")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      ipadd,message_reason = extract_ipadd()
      kernel_panic(ipadd,timestamp)
      os.system('logger -t montag -p user.info Sending email')
      os.system('logger -t montag -p user.info Process terminated')
      sys.exit(0)
elif sys.argv[1] == "limit_reached":
      print("call function Associated STA limit reached")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      ipadd,message_reason = extract_ipadd()
      limit_reached(ipadd,timestamp)
      os.system('logger -t montag -p user.info Sending email')
      os.system('logger -t montag -p user.info Process terminated')
      sys.exit(0)
else:
      os.system('logger -t montag -p user.info Wrong parameter received')
      sys.exit(2)

### stop process ###
sys.exit(0)
