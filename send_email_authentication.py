#!/usr/bin/env python

import sys
import os
import getopt
import json
import logging
import subprocess
from time import gmtime, strftime, localtime, sleep
#import requests
import datetime
import smtplib
import mimetypes
import re
from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from database_conf import *

script_name = sys.argv[0]
runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

# Get the System Name
uname = os.system('uname -a')
system_name = os.uname()[1].replace(" ", "_")

#Init Timestamp in second
timestamp = 300
timestamp = (timestamp/60)*100

def authentication_step1(ipadd,device_mac,auth_type,ssid,deassociation):
  write_api.write(bucket, org, [{"measurement": "support_wlan_association", "tags": {"AP_IPAddr": ipadd, "Client_MAC": device_mac, "Auth_type": auth_type, "Association": deassociation}, "fields": {"count": 1}}])
  if "0" in deassociation:
    message = "[{0}] WLAN deassociation detected from client {1} on Stellar AP {2} with Authentication type {3}".format(ssid,device_mac,ipadd,auth_type)
    os.system('logger -t montag -p user.info ' + message)

  else:
    message = "[{0}] WLAN association detected from client {1} on Stellar AP {2} with Authentication type {3}".format(ssid,device_mac,ipadd,auth_type)
    os.system('logger -t montag -p user.info ' + message)
    
def mac_authentication(device_mac_auth,ARP,source,reason):
  write_api.write(bucket, org, [{"measurement": "support_wlan_mac_auth", "tags": {"Client_MAC": device_mac_auth, "ARP": ARP, "Source": source, "Reason": reason}, "fields": {"count": 1}}])
  if "failed" in reason:
     message = "WLAN Authentication failed from client {0} assigned to {1} from {2}".format(device_mac_auth,ARP,source)
     os.system('logger -t montag -p user.info ' + message)
  elif "will" in reason:
     message = "WLAN Authentication success from client {0} assigned to {1} from {2}".format(device_mac_auth,ARP,source)
     os.system('logger -t montag -p user.info ' + message)
  else:
     message = "WLAN Authentication success from client {0} assigned to {1} from {2} - reason: {3}".format(device_mac_auth,ARP,source,reason)
     os.system('logger -t montag -p user.info ' + message)

def radius_authentication(auth_result,device_mac,accounting_status):
  write_api.write(bucket, org, [{"measurement": "support_wlan_radius_auth", "tags": {"Client_MAC": device_mac, "Auth_Result": auth_result, "Accounting_status": accounting_status}, "fields": {"count": 1}}])
  if "Failed" in auth_result:
      message = "WLAN 802.1x Authentication {0} for client {1}".format(auth_result,device_mac)
      os.system('logger -t montag -p user.info ' + message)
  if "Success" in auth_result:
      message = "WLAN 802.1x Authentication {0} for client {1}".format(auth_result,device_mac)
      os.system('logger -t montag -p user.info ' + message)
  if "null" in auth_result:
      os.system('logger -t montag -p user.info Radius authentication attempt or in progress')
  else:
     message = "WLAN 8021x Accounting {0} for {1}".format(accounting_status,device_mac)
     os.system('logger -t montag -p user.info ' + message)

def dhcp_ack(ipadd,device_mac):
  write_api.write(bucket, org, [{"measurement": "support_wlan_dhcp", "tags": {"Client_MAC": device_mac, "DHCP_Lease": ip_dhcp}, "fields": {"count": 1}}])
  message="DHCP Ack received with IP Address {0} for client {1}".format(ip_dhcp,device_mac)
  os.system('logger -t montag -p user.info ' + message)

def authentication_step2(ipadd,user_name,ssid):
  message = "[{0}] WLAN authentication on Captive Portal from User: {1} on Stellar AP {2}".format(ssid,user_name,ipadd)
  os.system('logger -t montag -p user.info ' + message)

def send_mail(timestamp,subject_content,message_content_1,message_content_2,ipadd):
# Send an email with log attached and last syslog message into the email body
  myDate = datetime.date.today()

  path_log_attachment = "/var/log/devices/{0}/syslog.log".format(ipadd)
  json_file = "/var/log/devices/{0}_{1}_history.json".format(ipadd,myDate.isoformat())

  content_variable = open (path_log_attachment,'r')
  file_lines = content_variable.readlines()
  content_variable.close()

  find_reason = open (json_file,'r')
  file_lines_reason = find_reason.readlines()
  find_reason.close()
  message_reason = file_lines_reason[-1]
  print(message_reason)
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

# Filter logs depending of the attribute received from Rsyslog
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


def radius_failover():
#open the file lastlog_8021X_authentication.json  and the Radius Authentication Server reachability
        pattern_Device_MAC = re.compile('.*\<(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\>.*')
        content_variable = open ('/var/log/devices/lastlog_8021X_authentication.json','r')
        file_lines = content_variable.readlines()
        content_variable.close()
        last_line = file_lines[-1]
        f=last_line.split(',')
        for element in f:
         if "RADIUS" in element:
           #In case of too many failed retransmit attempts, Radius Server is considered as unreachable
           if "too many failed retransmit attempts" in element:
             os.system('logger -t montag -p user.info Radius Server unreachable - too many failed retransmit attempts')
           if "No response from Authentication server" in element:
             os.system('logger -t montag -p user.info Primary Radius Server unreachable')
           if "failover" in element:
             os.system('logger -t montag -p user.info Failover to backup server')
             element_split = element.split(' ')
             for i in range(len(element_split)):
              if element_split[i]=="server":
                print("802.1x Authentication server unreachable")
                server = element_split[i+1]
                os.system('logger -t montag -p user.info Radius Server unreachable ' + server)
# Condition hardcoded to review once we have additionnal syslog messages in AWOS 4.0.4
           if "RADIUS Authentication server 10.130.7.25" in element:
             os.system('logger -t montag -p user.info Authentication sent to Backup Radius Server 10.130.7.25')

def extract_RADIUS_new():
  last = ""
  with open("/var/log/devices/lastlog_8021X_authentication.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

  with open("/var/log/devices/lastlog_8021X_authentication.json", "w", errors='ignore') as log_file:
    log_file.write(last)

  with open("/var/log/devices/lastlog_8021X_authentication.json", "r", errors='ignore') as log_file:
    log_json = json.load(log_file)
    ipadd = log_json["relayip"]
    host = log_json["hostname"]
    msg =log_json["message"]
    auth_result = "null"
    device_8021x_auth = accounting_status = "null"
    f=msg.split(',')
    for element in f:
       print(element)
       if "RADIUS" in element:
           if "RADIUS packet send to" in element:
             element_split = element.split(' ')
             for i in range(len(element_split)):
              if element_split[i]=="to":
                server = element_split[i+1]
                server = server.replace("\"","")
                os.system('logger -t montag -p user.info Authentication sent to Radius Server ' + server)
       if "8021x Authentication" in element:
        auth_result,device_8021x_auth = re.findall(r"8021x-Auth (.*?) for Sta<(.*?)>", msg)[0]
        print("Authentication success use case")
        # Wireless roam_trace[10065] <INFO> [AP DC:08:56:54:2D:40@10.130.7.76] [Employee_EAP @ ath11]: 8021x Authentication Success for Sta<de:ab:50:25:b8:71>
       if "8021x-Auth Failed" in element:
        auth_result = "Failed"
        device_8021x_auth = re.findall(r"STA <(.*?)>", msg)[0]
        print("Authentication failure use case")
        # Wireless roam_trace[10065] <INFO> [AP DC:08:56:54:2D:40@10.130.7.76] [Employee_EAP @ ath11]: 8021x-Auth Failed, STA <de:ab:50:25:b8:71> Disconnect
       if "8021x-Auth Accounting" in element:
        accounting_status,device_8021x_auth = re.findall(r"8021x-Auth Accounting (.*?) for STA <(.*?)>", msg)[0]
        auth_result = "0"
        print("accounting use case")
        # Wireless roam_trace[10065] <INFO> [AP DC:08:56:54:2D:40@10.130.7.76] [Employee_EAP @ ath11]: 8021x-Auth Accounting start for STA <de:ab:50:25:b8:71> 
       print(auth_result)
       print(device_8021x_auth)
       print(accounting_status)
  return auth_result,device_8021x_auth,accounting_status;

def extract_WCF():
        pattern_Device_MAC = re.compile('.*\[(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\].*')
        pattern_FQDN = re.compile('(fqdn:\[(.*?)\])')
        pattern_domain = re.compile('(domain:\[(.*?)\])')
        content_variable = open ('/var/log/devices/lastlog_wcf.json','r')
        file_lines = content_variable.readlines()
        content_variable.close()
        last_line = file_lines[-1]
        f=last_line.split(',')
        # Variables initialized to null
        domain = device_mac_wcf = fqdn = "null"
        print("Extract WCF function")
        for element in f:
         if "Add dns domain" in element:
          domain = re.search(pattern_domain, str(f)).group(1)
          print(domain)
          message = "{0} added in AP cache".format(domain)
          os.system('logger -t montag -p user.info  ' + message)
         if "<ALERT>" in element:
          device_mac_wcf = re.search(pattern_Device_MAC, str(f)).group(1)
          fqdn = re.search(pattern_FQDN, str(f)).group(1)
          print("WCF Block FQDN: " + fqdn)
          message = "Web Content Filtering for device {0} when accessing Site {1}".format(device_mac_wcf,fqdn)
          os.system('logger -t montag -p user.info  ' + message)
          write_api.write(bucket, org, [{"measurement": "support_wlan_wcf", "tags": {"Client_MAC": device_mac_wcf, "URL": fqdn}, "fields": {"count": 1}}])

def extract_ARP():
#open the file lastlog_mac_authentication.json  and and get the Access Role Profile + result + source
        pattern_Device_MAC = re.compile('.*\<(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\>.*')
        content_variable = open ('/var/log/devices/lastlog_mac_authentication.json','r')
        file_lines = content_variable.readlines()
        content_variable.close()
        last_line = file_lines[-1]
        f=last_line.split(',')
        # Variables initialized to null
        device_mac_auth = ARP = source = reason = "null"
        for element in f:
         if "enforcement" in element or "updated" in element:
        # Variables initialized to default values
          source = "IoT"
          reason = "Enforcement"
          device_mac_auth = re.search(pattern_Device_MAC, str(f)).group(1)
          element_split = element.split(' ')
          for i in range(len(element_split)):
            if element_split[i]=="Role":
              print("Access Role assigned")
              ARP = element_split[i+1]
              ARP = ARP.replace("(", " ",2).replace(")", " ",2)
 
         elif "Access Role" in element:
          device_mac_auth = re.search(pattern_Device_MAC, str(f)).group(1)
          element_split = element.split(' ')
          for i in range(len(element_split)):
             if element_split[i]=="Access":
              print("Access Role assigned")
              ARP = element_split[i+1]
              ARP = ARP.replace("(", " ",2).replace(")", " ",2)

             elif element_split[i]=="Role":
              print("Access Role assigned")
              ARP = element_split[i+1]
              ARP = ARP.replace("(", " ",2).replace(")", " ",2)

             if element_split[i]=="from":
              source = element_split[i+1]
              source = source.replace("(", " ",2).replace(")", " ",2)
              if element_split[i+2]=="(MAC-Auth":
                reason = element_split[i+2] + " " + element_split[i+3]
                reason = reason.replace("(", " ",2).replace(")", " ",2)

              else:
                reason = element_split[i+2]
                reason = reason.replace("(", " ",2).replace(")", " ",2)
        return ARP,device_mac_auth,source,reason;

def extract_Policy():
#open the file lastlog_policy.json and get the Policy List assigned to client + Location Policy/Period check
        pattern_Device_MAC = re.compile('.*\<(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\>.*')
        content_variable = open ('/var/log/devices/lastlog_policy.json','r')
        file_lines = content_variable.readlines()
        content_variable.close()
        last_line = file_lines[-1]
        f=last_line.split(',')
        # Variables initialized to null
        Policy = "null"
        for element in f:
         if "PolicyList" in element:
            element_split = element.split(' ')
            for i in range(len(element_split)):
             if element_split[i]=="PolicyList":
              print("Policy assigned")
              Policy = element_split[i+3]
              Policy = Policy.replace("[", " ",2).replace("]", " ",2).replace("\"", " ",2)
              os.system('logger -t montag -p user.info Policy List applied: ' + Policy)
        ### If Location Policy check fails ####
         if "check Failed" in element:
            os.system('logger -t montag -p user.info Location Policy not authorized')
        ### If Location Period check fails ####
         if "current time is not allowed to access" in element:
            os.system('logger -t montag -p user.info Access to SSID not authorized as per Period Policy')
        return Policy;

def extract_ip_dhcp():
#open the file lastlog_dhcp.json  and check if the DHCPACK with DHCP Lease is received
        pattern_Device_MAC = re.compile('.*\<(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\>.*')
        content_variable = open ('/var/log/devices/lastlog_dhcp.json','r')
        file_lines = content_variable.readlines()
        content_variable.close()
        last_line = file_lines[-1]
        f=last_line.split(',')
        # Variables initialized to null
        ip_dhcp = "null"
        for element in f:
          if "DHCPACK" or "dhcp ack" in element:
            element_split = element.split(' ')
            for i in range(len(element_split)):
             if element_split[i]=="address":
              print("DHCP Lease received")
              ip_dhcp = element_split[i+1]
              ip_dhcp = ip_dhcp.strip(" \"\\")
        return ip_dhcp;

def extract_ip_port():
#open the file lastlog_wlan_authentication.json  and get the AP IP Address + Client MAC Address + Authentication type + SSID
        pattern_AP_MAC = re.compile('.*\((([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\).*')
        pattern_Device_MAC = re.compile('.*\[(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\].*')
        content_variable = open ('/var/log/devices/lastlog_wlan_authentication.json','r')
        file_lines = content_variable.readlines()
        content_variable.close()
        last_line = file_lines[-1]
        f=last_line.split(',')
        #For each element, look if relayip is present. If yes,  separate the text and the ip address
        for element in f:
         if "relayip" in element:
           element_split = element.split(':')
           ipadd_quot = element_split[1]
           ipadd = ipadd_quot[-len(ipadd_quot)+1:-1]
        # Variables initialized to null
           device_mac= ap_mac = reason = auth_type = user_name = ssid = deassociation = "null"
         #For each element, look if reason is present, if yes, we take the AP MAC Address and the Device MAC Address
         if "SSID" in element:
            print("SSID in element")
            element_split = element.split()
            for i in range(len(element_split)):
             if element_split[i]=="SSID":
              ssid = element_split[i+2]
              ssid = ssid.strip(" []")
              print(ssid)

         if "AuthType" in element:
            print("AuthType in element")
            device_mac = re.search(pattern_Device_MAC, str(f)).group(1)
            element_split = element.split()
            for i in range(len(element_split)):
             if element_split[i]=="AuthType":
              auth_type = element_split[i+1]
              auth_type = auth_type.strip(" ()")
              auth_type = auth_type.replace("}", "]", 1)

         if "status" in element:
               print("Association status in element")
               device_mac = re.search(pattern_Device_MAC, str(f)).group(1)
               element_split = element.split()
               for i in range(len(element_split)):
                if element_split[i]=="status":
                  deassociation = element_split[i+1]
                  deassociation = deassociation.strip(" []")

         if "Portalname" in element:
            device_mac = re.search(pattern_Device_MAC, str(f)).group(1)
            element_split = element.split()
            for i in range(len(element_split)):
             if element_split[i]=="Portalname":
              user_name = element_split[i+1]
              user_name = user_name.replace("(", " ", 1)
        return ipadd,device_mac,ap_mac,auth_type,user_name,ssid,deassociation;

def get_credentials():
     content_variable = open ('/opt/ALE_Script/ALE_script.conf','r')
     file_lines = content_variable.readlines()
     content_variable.close()
     credentials_line = file_lines[0]
     credentials_line_split = credentials_line.split(',')
     user = credentials_line_split[0]
     password = credentials_line_split[1]
     if credentials_line_split[3] != "":
        id= '&jid1=' + credentials_line_split[3]
     elif credentials_line_split[3] == "":
        id=''

     gmail_usr = credentials_line_split[4]
     gmail_passwd = credentials_line_split[5]
     mails = credentials_line_split[2].split(';')
     mails = [ element  for element  in mails]
     return user,password,id,gmail_usr,gmail_passwd,mails

#ipadd,device_mac,ap_mac,auth_type,user_name,ssid,deassociation = extract_ip_port()   #returning relayIP and port number where loop detected
#arp,device_mac_auth,source,reason = extract_ARP() #return Access role Profile and Device authenticated
#ip_dhcp = extract_ip_dhcp()
#auth_result,device_8021x_auth,accounting_status = extract_RADIUS()
user,password,jid,gmail_user,gmail_password,mails = get_credentials()

## if $msg contains 'Recv the  wam module  notify  data user'##
if sys.argv[1] == "auth_step1":
      print("call function authentication step1")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      ipadd,device_mac,ap_mac,auth_type,user_name,ssid,deassociation = extract_ip_port()
      authentication_step1(ipadd,device_mac,auth_type,ssid,deassociation)
      sys.exit(0)

## if $msg contains ':authorize' or $msg contains 'from MAC-Auth' or $msg contains 'Access Role'##
##    if $msg contains 'Access Role(' ##
if sys.argv[1] == "mac_auth":
      print("call function mac_authentication")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      arp,device_mac_auth,source,reason = extract_ARP()
      mac_authentication(device_mac_auth,arp,source,reason)
      sys.exit(0)

## if $msg contains '8021x-Auth' or $msg contains 'RADIUS' or $msg contains '8021x Authentication' ##
if sys.argv[1] == "8021X":
      print("call function radius_authentication")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      auth_result,device_8021x_auth,accounting_status = extract_RADIUS_new()
      radius_authentication(auth_result,device_8021x_auth,accounting_status)
      sys.exit(0)

##    if $msg contains 'too many failed retransmit attempts' or $msg contains 'No response'
if sys.argv[1] == "failover":
      print("call function radius_failover")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      radius_failover()
      sys.exit(0)

## if $msg contains ':authorize' or $msg contains 'from MAC-Auth' or $msg contains 'Access Role'##
##     if $msg contains 'Get PolicyList' ##
## OR if $msg contains 'check period policy' or $msg contains 'Loaction Policy' ##
if sys.argv[1] == "policy":
      print("call function policy")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      extract_Policy()
      sys.exit(0)

## if $msg contains 'Found DHCPACK for STA'  or $msg contains 'Found dhcp ack for STA'##
if sys.argv[1] == "dhcp":
      print("call function dhcp_ack")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      ipadd,device_mac,ap_mac,auth_type,user_name,ssid,deassociation = extract_ip_port()
      ip_dhcp = extract_ip_dhcp()
      dhcp_ack(ipadd,device_mac)
      sys.exit(0)

## if $msg contains 'verdict:[NF_DROP]' #
if sys.argv[1] == "wcf_block":
      print("call function wcf_block")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      extract_WCF()
      sys.exit(0)

## if $msg contains 'Recv the  eag module  notify  data user' ##
if sys.argv[1] == "auth_step2":
      print("call function authentication step2")
      os.system('logger -t montag -p user.info Variable received from rsyslog ' + sys.argv[1])
      ipadd,device_mac,ap_mac,auth_type,user_name,ssid,deassociation = extract_ip_port()
      authentication_step2(ipadd,user_name,ssid)
      sys.exit(0)
else:
      os.system('logger -t montag -p user.info Wrong parameter received' + sys.argv[1])
      sys.exit(2)

### stop process ###
sys.exit(0)

