#!/usr/bin/env python
import sys
import os
import getopt
import json
import logging
import subprocess
import requests
from time import gmtime, strftime, localtime, sleep
import smtplib
from support_tools import save_attachment
import mimetypes
import re
from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from support_web_receiver_class import Receiver,start_web
from database_conf import *

def send_message(info,jid):
    """ 
    Send the message in info to a Rainbowbot. This bot will send this message to the jid in parameters

    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :return:                        None
    """


    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Classic_EMEA"
    headers = {'Content-type': 'application/json', "Accept-Charset": "UTF-8", 'jid1': '{0}'.format(jid), 'toto': '{0}'.format(info),'Card': '0'}
    response = requests.get(url, headers=headers)
    write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])

def send_alert(info,jid):
    """
    Send the message in info to a Rainbowbot. This bot will send this message to the jid in parameters

    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :return:                        None
    """


    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Alert_EMEA"
    headers = {'Content-type': 'application/json', "Accept-Charset": "UTF-8", 'jid1': '{0}'.format(jid), 'toto': '{0}'.format(info),'Card': '0'}
    response = requests.get(url, headers=headers)
    write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response}, "fields": {"count": 1}}])

def send_message_aijaz(subject,info,jid):
    """
    Send the message in info to a Rainbowbot. This bot will send this message to the jid in parameters

    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :return:                        None
    """


    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Aijaz"
    headers = {'Content-type': 'application/json', "Accept-Charset": "UTF-8", 'jid1': '{0}'.format(jid), 'tata': '{0}'.format(subject),'toto': '{0}'.format(info), 'Card': '0'}
    response = requests.get(url, headers=headers)
    write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "No"}, "fields": {"count": 1}}])

def send_message_request(info,jid,receiver):
    """ 
    Send the message, with a URL requests  to a Rainbowbot. This bot will send this message and request to the jid in parameters

    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :param str ip_server:           IP Adress of the server log , which is also a web server
    :param str id_client:           Unique ID creates during the Setup.sh, to identifie the URL request to the good client
    :param str id_case:             Unique ID creates during the response_handler , to identifie the URL request to the good case.
    :return:                        None
    """

    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Classic_EMEA"
    headers = {'Content-type': 'application/json', "Accept-Charset": "UTF-8",'Card': '1', 'jid1': '{0}'.format(jid), 'toto': '{0}.'.format(info)}
    response = requests.get(url, headers=headers)
    write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response, "Rainbow Card": "Yes"}, "fields": {"count": 1}}])
    print(response.text)
    receiver.set_answer(response.text)
    sleep(1)
    url = "http://127.0.0.1:5200/?id=rainbow"
    response = requests.get(url)

def send_file(info,jid,ipadd,filename_path =''):
    """ 
    Send the attachement to a Rainbowbot. This bot will send this file to the jid in parameters
    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :param str ipadd:               IP Address of the device concerned by the issue 
    :return:                        None
    """


#    if re.search("A Pattern has been detected in switch",info) :
#       cmd = "ls -t /tftpboot/"
#       run=cmd.split()
#       p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
#       p = subprocess.Popen(('grep',ipadd),stdin=p.stdout, stdout=subprocess.PIPE)
#       p =  subprocess.Popen(('head','-n','1'),stdin=p.stdout,stdout=subprocess.PIPE)
#       out, err = p.communicate()
#       out=out.decode('UTF-8').strip()

#       fp = open("/tftpboot/{0}".format(out),'rb')
#       info = "Log of device : {0}".format(ipadd)
#       url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotifFile/"
#       headers = { 'Content-Transfer-Encoding': 'application/gzip', 'jid1': '{0}'.format(jid),'toto': '{0}'.format(info)}
#       files = {'file': open('/tftpboot/{0}'.format(out),'rb')}
#       params = {'filename'  :'{0}'.format(out)}
#       response = requests.post(url,files=files,params=params, headers=headers)

    if not filename_path =='':
       payload=open("{0}".format(filename_path),'rb')
       filename = filename_path.split("/")
       filename = filename[-1]
       info = "Log of device : {0}".format(ipadd)
       url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_File_EMEA"
       headers = {  'Content-type':"application/x-tar",'Content-Disposition': "attachment;filename={0}".format(filename), 'jid1': '{0}'.format(jid),'toto': '{0}'.format(info)}
       #files = {'file': fp}
       response = requests.post(url, headers=headers, data=payload)
       print(response)
       write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response}, "fields": {"count": 1}}])


    save_attachment(ipadd)
    info = "Log of device : {0}".format(ipadd)

    with open("/var/log/devices/attachment.log", "r+", errors='ignore') as log_file:
        for line in log_file:
            timestamp = ""
            if re.search(r"\d?\d \d\d:\d\d:\d\d", line):
                timestamp = re.findall(r"\d?\d \d\d:\d\d:\d\d", line)[0]
                break
        if re.search(r"\d?\d (\d\d):(\d\d):(\d\d)", timestamp):
            hour, min, sec = re.findall(r"\d?\d (\d\d):(\d\d):(\d\d)", timestamp)[0]
            sec = int(sec) + 80
            if sec > 60:
                min = int(min) + 1
                sec -= 60
        else:
            hour, min, sec = (24, 59, 59)
    
        new_file = ""
        for line in log_file:
            if re.search(r"\d?\d \d\d:\d\d:\d\d", line):
                timestamp = re.findall(r"\d?\d \d\d:\d\d:\d\d", line)[0]
                new_hour, new_min, new_sec = re.findall(r"\d?\d (\d\d):(\d\d):(\d\d)", str(timestamp))[0]
                new_file += line
                if int(new_hour) >= int(hour) and int(new_min) >= int(min) and int(new_sec) >= int(sec):
                    break
    
    with open("/var/log/devices/short_attachment.log", "w+", errors='ignore') as s_log:
        print(new_file)
        s_log.write(new_file)



    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_File_EMEA"
    headers = {  'Content-type':"text/plain",'Content-Disposition': "attachment;filename=short_attachment.log", 'jid1': '{0}'.format(jid),'toto': '{0}'.format(info)}
    files = {'file': open('/var/log/devices/short_attachment.log','r')}
    response = requests.post(url,files=files, headers=headers)
    write_api.write(bucket, org, [{"measurement": "support_send_notification", "tags": {"HTTP_Request": url, "HTTP_Response": response}, "fields": {"count": 1}}])
    sleep(5)





def send_mail_request(ip_switch_1,ip_switch_2,info,subject,gmail_user,gmail_password,mails,ip_server,id_client,id_case):

 # logging.basicConfig(filename='/opt/ALE_script/send_email.log', filemode='w', level=logging.DEBUG)

  runtime = strftime("%d_%b_%Y_%H_%M_%S_0000", localtime())
  uname = os.system('uname -a')
  system_name = os.uname()[1].replace(" ", "_")
  logging.info("Running on {0} at {1} ".format(system_name, runtime))


  #attachment configuration
  if ip_switch_1 != "0":
     save_attachment(ip_switch_1)
     fp = open('/var/log/devices/attachment.log','r')

     part3 = MIMEBase('application', "octet-stream")
     part3.set_payload((fp).read())
     fp.close()
     encoders.encode_base64(part3)
     part3.add_header( 'Content-Disposition', 'attachment',  filename= "{0}_attachment.log".format(ip_switch_1))

  if ip_switch_2 != "0":
      save_attachment(ip_switch_2)
      fp = open('/var/log/devices/attachment.log','r')

      part4 = MIMEBase('application', "octet-stream")
      part4.set_payload((fp).read())
      fp.close()
      encoders.encode_base64(part4)
      part4.add_header( 'Content-Disposition', 'attachment',  filename= "{0}_attachment.log".format(ip_switch_2))
  #add part to send log tar file
  for mail in mails:
   #email account properties
   #email properties
   sent_from = gmail_user
   to = mail

   ### Ajout support MIME
   message = MIMEMultipart("alternative")
   message["Subject"] = "{0}".format(subject)
   message["From"] = sent_from
   message["To"] = to

   email_text = """\
   Subject: Link down

   Hello
   This email to notify {0}.""".format(info)


   yes_link="10.130.7.14:5200?id=01234567890012345678&answer=no"
   email_html = """\
   <html>
     <body>
       <p>
         This email to notify {0}.<br>
          <br>
          Do you want to fix it? 
         <li> <a href="http://{1}:5200?id={2}{3}&answer=yes" >Yes</a></li>
         <li> <a href="http://{1}:5200?id={2}{3}&answer=no" >No</a></li>
         <li> <a href="http://{1}:5200?id={2}{3}&answer=save" >Yes, and remember</a><br>
          </li><br>
       </p>
<table class=Tabellanormale border=0 cellpadding=0 align=left width=100 style='width:75.0pt'><tr><td style='border:none;border-top:solid #6B489D 4.5pt;padding:.75pt .75pt .75pt .75pt'></td></tr></table><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 width="100%" style='width:100.0%;background:white'><tr><td valign=top style='padding:0cm 0cm 0cm 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 width="100%" style='width:100.0%'><tr><td valign=top style='padding:11.25pt 0cm 11.25pt 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 width="100%" style='width:100.0%'><tr><td valign=top style='padding:0cm 0cm 0cm 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 width="100%" style='width:100.0%'><tr><td valign=top style='padding:0cm 0cm 0cm 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 align=left width=420 style='width:315.0pt'><tr><td valign=top style='padding:0cm 0cm 0cm 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 align=left><tr><td style='padding:0cm 0cm 0cm 0cm'><p class=MsoNormal><b><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#6B489D'>NBD Support Team<o:p></o:p></span></b></p></td></tr><tr><td style='padding:0cm 0cm 7.5pt 0cm'><p class=MsoNormal style='line-height:13.5pt'><span style='font-size:10.0pt;font-family:ClanOT-Book;color:black'>Alcatel-Lucent Enterprise <o:p></o:p></span></p></td></tr><tr><td style='padding:0cm 0cm 7.5pt 0cm'><p class=MsoNormal><span style='font-size:10.0pt;font-family:ClanOT-Book;color:black'><o:p></o:p></span></p><p class=MsoNormal><span style='font-size:10.0pt;font-family:ClanOT-Book;color:black'><o:p>&nbsp;</o:p></span></p><p class=MsoNormal><b><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#6B489D'><a href="https://web.openrainbow.com/" target="_blank"><span style='color:#6B489D;border:none windowtext 1.0pt;padding:0cm'>Rainbow collaboration platform</span><span style='color:#6B489D;border:none windowtext 1.0pt;padding:0cm;font-weight:normal'> </span></a><o:p></o:p></span></b></p></td></tr><tr><td style='padding:0cm 0cm 0cm 0cm'><p class=MsoNormal style='line-height:13.5pt'><span style='font-size:10.0pt;font-family:ClanOT-Book;color:black'>ALE International <o:p></o:p></span></p></td></tr><tr><td style='padding:0cm 0cm 0cm 0cm'><p class=MsoNormal style='line-height:13.5pt'><span lang=FR style='font-size:10.0pt;font-family:ClanOT-Book;color:black'>115-225 rue A. de St-Exupery<o:p></o:p></span></p><p class=MsoNormal style='line-height:13.5pt'><span lang=FR style='font-size:10.0pt;font-family:ClanOT-Book;color:black'>ZAC Prat Pip - Guipavas<o:p></o:p></span></p></td></tr><tr style='height:60.9pt'><td style='padding:0cm 0cm 7.5pt 0cm;height:60.9pt'><p class=MsoNormal style='line-height:13.5pt'><span style='font-size:10.0pt;font-family:ClanOT-Book;color:black'>29806 BREST, France</span><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#3A3A3A'> <o:p></o:p></span></p><p class=MsoNormal style='line-height:13.5pt'><span style='font-size:10.0pt'><a href="https://www.al-enterprise.com/"><span style='font-family:ClanOT-Book;color:#3A3A3A;text-decoration:none'><img border=0 width=173 height=76 style='width:1.802in;height:.7916in' id="Picture_x0020_1" src="cid:image009.png@01D72707.92BFB2D0" alt="https://www.al-enterprise.com/-/media/assets/internet/images/h-to-m/logo-389x170.png"></span></a></span><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#3A3A3A'><o:p></o:p></span></p><p class=MsoNormal style='line-height:13.5pt'><span style='font-size:10.0pt'><a href="https://www.linkedin.com/company/alcatellucententerprise/"><span style='font-family:ClanOT-Book;color:#3A3A3A;text-decoration:none'><img border=0 width=30 height=30 style='width:.3125in;height:.3125in' id="Picture_x0020_39" src="cid:image010.png@01D72707.92BFB2D0" alt="https://www.al-enterprise.com/-/media/assets/internet/images/h-to-m/in-1080x1080.png"></span></a></span><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#3A3A3A'> </span><span style='font-size:10.0pt'><a href="https://twitter.com/ALUEnterprise"><span style='font-family:ClanOT-Book;color:#3A3A3A;text-decoration:none'><img border=0 width=30 height=30 style='width:.3125in;height:.3125in' id="Picture_x0020_40" src="cid:image011.png@01D72707.92BFB2D0" alt="https://www.al-enterprise.com/-/media/assets/internet/images/t-to-z/tw-1080x1080.png"></span></a></span><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#3A3A3A'> </span><span style='font-size:10.0pt'><a href="https://www.facebook.com/ALUEnterprise"><span style='font-family:ClanOT-Book;color:#3A3A3A;text-decoration:none'><img border=0 width=30 height=30 style='width:.3125in;height:.3125in' id="Picture_x0020_41" src="cid:image012.png@01D72707.92BFB2D0" alt="https://www.al-enterprise.com/-/media/assets/internet/images/a-to-g/fb-1080x1080.png"></span></a></span><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#3A3A3A'><o:p></o:p></span></p></td></tr><tr><td style='padding:0cm 0cm 0cm 0cm'></td></tr></table></td></tr></table></td></tr></table></td></tr><tr><td valign=top style='padding:0cm 0cm 0cm 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 width="100%" style='width:100.0%'><tr><td valign=top style='padding:3.75pt 0cm 0cm 0cm'><p class=MsoNormal style='text-align:justify;text-justify:inter-ideograph;line-height:12.0pt'><span style='font-size:7.0pt;font-family:ClanOT-Book;color:#BBBCBC'>The Alcatel-Lucent name and logo are trademarks of Nokia used under license by ALE. <o:p></o:p></span></p><p class=MsoNormal style='text-align:justify;text-justify:inter-ideograph;line-height:12.0pt'><span style='font-size:7.0pt;font-family:ClanOT-Book;color:#BBBCBC'>This communication is intended to be received only by the individual or entity to whom or to which it is addressed and may contain information that is privileged, is confidential and is subject to copyright. Any unauthorized use, copying, review or disclosure of this communication is strictly prohibited. If you have received this communication in error, please delete this message from your email box and information system (including all files and documents attached) and notify the sender by reply email. Please consider protecting the environment before printing. Thank you for your cooperation.</span><span style='font-size:7.0pt;font-family:ClanOT-Book;color:#B8B8B8'> </span><span style='font-size:8.5pt;font-family:ClanOT-Book;color:#B8B8B8'><o:p></o:p></span></p></td></tr></table></td></tr></table></td></tr></table></td></tr></table><p class=MsoNormal><o:p>&nbsp;</o:p></p><p class=MsoNormal><o:p>&nbsp;</o:p></p></div>
     </body>
   </html>   """.format(info,ip_server,id_client,id_case)

   # Turn these into plain/html MIMEText objects
   part1 = MIMEText(email_text, "plain")
   part2 = MIMEText(email_html, "html")

   # Add HTML/plain-text parts to MIMEMultipart message
   # The email client will try to render the last part first
   message.attach(part1)
   message.attach(part2)
   if ip_switch_1 != "0":
     message.attach(part3)
   if ip_switch_2 != "0":
      message.attach(part4)


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





def send_mail(ip_switch_1,ip_switch_2,info,subject,gmail_user,gmail_password,mails,timestamp = 0 ,mac = "0" ):

 # logging.basicConfig(filename='/opt/ALE_script/send_email.log', filemode='w', level=logging.DEBUG)

  runtime = strftime("%d_%b_%Y_%H_%M_%S_0000", localtime())
  uname = os.system('uname -a')
  system_name = os.uname()[1].replace(" ", "_")
  logging.info("Running on {0} at {1} ".format(system_name, runtime))

  #attachment configuration
  if ip_switch_1 != "0":
     if timestamp == 0:
        save_attachment(ip_switch_1)
     else:
        save_attachment_deauth(ip_switch_1,mac,timestamp)

     fp = open('/var/log/devices/attachment.log','r')

     part3 = MIMEBase('application', "octet-stream")
     part3.set_payload((fp).read())
     fp.close()
     encoders.encode_base64(part3)
     part3.add_header( 'Content-Disposition', 'attachment',  filename= "{0}_attachment.log".format(ip_switch_1))

  if ip_switch_2 != "0":
      save_attachment(ip_switch_2)
      fp = open('/var/log/devices/attachment.log','r')

      part4 = MIMEBase('application', "octet-stream")
      part4.set_payload((fp).read())
      fp.close()
      encoders.encode_base64(part4)
      part4.add_header( 'Content-Disposition', 'attachment',  filename= "{0}_attachment.log".format(ip_switch_2))
  if re.search("A Pattern has been detected in switch",subject) :

     cmd = "ls -t /tftpboot/"
     run=cmd.split()
     p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
     p = subprocess.Popen(('grep',ip_switch_1),stdin=p.stdout, stdout=subprocess.PIPE)
     p =  subprocess.Popen(('head','-n','1'),stdin=p.stdout,stdout=subprocess.PIPE)
     out, err = p.communicate()
     out=out.decode('UTF-8').strip()

     part5= MIMEBase('application', 'tar')
     fp = open("/tftpboot/{0}".format(out),'rb')
     part5.set_payload(fp.read())
     encoders.encode_base64(part5)
     part5.add_header('Content-Disposition', 'attachment',filename=out)

 
     cmd = "ls -t /opt/ALE_Script"
     run=cmd.split()
     p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
     p = subprocess.Popen(('grep',ip_switch_1),stdin=p.stdout, stdout=subprocess.PIPE)
     p =  subprocess.Popen(('head','-n','1'),stdin=p.stdout,stdout=subprocess.PIPE)
     out, err = p.communicate()
     out=out.decode('UTF-8').strip()

     part6= MIMEBase('application', 'txt')
     fp = open("/opt/ALE_Script/{0}".format(out),'rb')
     part6.set_payload(fp.read())
     encoders.encode_base64(part5)
     part6.add_header('Content-Disposition', 'attachment',filename=out)

     cmd = "rm -rf /opt/ALE_Script/{0}".format(out)
     run=cmd.split()
     p = subprocess.Popen(run, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)




  for mail in mails:
   #email account properties
   #email properties
   sent_from = gmail_user
   to = mail

   ### Ajout support MIME
   message = MIMEMultipart("alternative")
   message["Subject"] = "{0}".format(subject)
   message["From"] = sent_from
   message["To"] = to

   email_text = """\
   Subject: Link down

   Hello
   This email to notify {0}.""".format(info)


   email_html = """\
   <html>
     <body>
       <p>
       <br>   Hello </br>
          This email to notify {0}.
       </p>
<table class=Tabellanormale border=0 cellpadding=0 align=left width=100 style='width:75.0pt'><tr><td style='border:none;border-top:solid #6B489D 4.5pt;padding:.75pt .75pt .75pt .75pt'></td></tr></table><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 width="100%" style='width:100.0%;background:white'><tr><td valign=top style='padding:0cm 0cm 0cm 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 width="100%" style='width:100.0%'><tr><td valign=top style='padding:11.25pt 0cm 11.25pt 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 width="100%" style='width:100.0%'><tr><td valign=top style='padding:0cm 0cm 0cm 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 width="100%" style='width:100.0%'><tr><td valign=top style='padding:0cm 0cm 0cm 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 align=left width=420 style='width:315.0pt'><tr><td valign=top style='padding:0cm 0cm 0cm 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 align=left><tr><td style='padding:0cm 0cm 0cm 0cm'><p class=MsoNormal><b><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#6B489D'>NBD Support Team<o:p></o:p></span></b></p></td></tr><tr><td style='padding:0cm 0cm 7.5pt 0cm'><p class=MsoNormal style='line-height:13.5pt'><span style='font-size:10.0pt;font-family:ClanOT-Book;color:black'>Alcatel-Lucent Enterprise <o:p></o:p></span></p></td></tr><tr><td style='padding:0cm 0cm 7.5pt 0cm'><p class=MsoNormal><span style='font-size:10.0pt;font-family:ClanOT-Book;color:black'><o:p></o:p></span></p><p class=MsoNormal><span style='font-size:10.0pt;font-family:ClanOT-Book;color:black'><o:p>&nbsp;</o:p></span></p><p class=MsoNormal><b><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#6B489D'><a href="https://web.openrainbow.com/" target="_blank"><span style='color:#6B489D;border:none windowtext 1.0pt;padding:0cm'>Rainbow collaboration platform</span><span style='color:#6B489D;border:none windowtext 1.0pt;padding:0cm;font-weight:normal'> </span></a><o:p></o:p></span></b></p></td></tr><tr><td style='padding:0cm 0cm 0cm 0cm'><p class=MsoNormal style='line-height:13.5pt'><span style='font-size:10.0pt;font-family:ClanOT-Book;color:black'>ALE International <o:p></o:p></span></p></td></tr><tr><td style='padding:0cm 0cm 0cm 0cm'><p class=MsoNormal style='line-height:13.5pt'><span lang=FR style='font-size:10.0pt;font-family:ClanOT-Book;color:black'>115-225 rue A. de St-Exupery<o:p></o:p></span></p><p class=MsoNormal style='line-height:13.5pt'><span lang=FR style='font-size:10.0pt;font-family:ClanOT-Book;color:black'>ZAC Prat Pip - Guipavas<o:p></o:p></span></p></td></tr><tr style='height:60.9pt'><td style='padding:0cm 0cm 7.5pt 0cm;height:60.9pt'><p class=MsoNormal style='line-height:13.5pt'><span style='font-size:10.0pt;font-family:ClanOT-Book;color:black'>29806 BREST, France</span><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#3A3A3A'> <o:p></o:p></span></p><p class=MsoNormal style='line-height:13.5pt'><span style='font-size:10.0pt'><a href="https://www.al-enterprise.com/"><span style='font-family:ClanOT-Book;color:#3A3A3A;text-decoration:none'><img border=0 width=173 height=76 style='width:1.802in;height:.7916in' id="Picture_x0020_1" src="cid:image009.png@01D72707.92BFB2D0" alt="https://www.al-enterprise.com/-/media/assets/internet/images/h-to-m/logo-389x170.png"></span></a></span><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#3A3A3A'><o:p></o:p></span></p><p class=MsoNormal style='line-height:13.5pt'><span style='font-size:10.0pt'><a href="https://www.linkedin.com/company/alcatellucententerprise/"><span style='font-family:ClanOT-Book;color:#3A3A3A;text-decoration:none'><img border=0 width=30 height=30 style='width:.3125in;height:.3125in' id="Picture_x0020_39" src="cid:image010.png@01D72707.92BFB2D0" alt="https://www.al-enterprise.com/-/media/assets/internet/images/h-to-m/in-1080x1080.png"></span></a></span><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#3A3A3A'> </span><span style='font-size:10.0pt'><a href="https://twitter.com/ALUEnterprise"><span style='font-family:ClanOT-Book;color:#3A3A3A;text-decoration:none'><img border=0 width=30 height=30 style='width:.3125in;height:.3125in' id="Picture_x0020_40" src="cid:image011.png@01D72707.92BFB2D0" alt="https://www.al-enterprise.com/-/media/assets/internet/images/t-to-z/tw-1080x1080.png"></span></a></span><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#3A3A3A'> </span><span style='font-size:10.0pt'><a href="https://www.facebook.com/ALUEnterprise"><span style='font-family:ClanOT-Book;color:#3A3A3A;text-decoration:none'><img border=0 width=30 height=30 style='width:.3125in;height:.3125in' id="Picture_x0020_41" src="cid:image012.png@01D72707.92BFB2D0" alt="https://www.al-enterprise.com/-/media/assets/internet/images/a-to-g/fb-1080x1080.png"></span></a></span><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#3A3A3A'><o:p></o:p></span></p></td></tr><tr><td style='padding:0cm 0cm 0cm 0cm'></td></tr></table></td></tr></table></td></tr></table></td></tr><tr><td valign=top style='padding:0cm 0cm 0cm 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 width="100%" style='width:100.0%'><tr><td valign=top style='padding:3.75pt 0cm 0cm 0cm'><p class=MsoNormal style='text-align:justify;text-justify:inter-ideograph;line-height:12.0pt'><span style='font-size:7.0pt;font-family:ClanOT-Book;color:#BBBCBC'>The Alcatel-Lucent name and logo are trademarks of Nokia used under license by ALE. <o:p></o:p></span></p><p class=MsoNormal style='text-align:justify;text-justify:inter-ideograph;line-height:12.0pt'><span style='font-size:7.0pt;font-family:ClanOT-Book;color:#BBBCBC'>This communication is intended to be received only by the individual or entity to whom or to which it is addressed and may contain information that is privileged, is confidential and is subject to copyright. Any unauthorized use, copying, review or disclosure of this communication is strictly prohibited. If you have received this communication in error, please delete this message from your email box and information system (including all files and documents attached) and notify the sender by reply email. Please consider protecting the environment before printing. Thank you for your cooperation.</span><span style='font-size:7.0pt;font-family:ClanOT-Book;color:#B8B8B8'> </span><span style='font-size:8.5pt;font-family:ClanOT-Book;color:#B8B8B8'><o:p></o:p></span></p></td></tr></table></td></tr></table></td></tr></table></td></tr></table><p class=MsoNormal><o:p>&nbsp;</o:p></p><p class=MsoNormal><o:p>&nbsp;</o:p></p></div>
     </body>
   </html>   """.format(info)

   # Turn these into plain/html MIMEText objects
   part1 = MIMEText(email_text, "plain")
   part2 = MIMEText(email_html, "html")

   # Add HTML/plain-text parts to MIMEMultipart message
   # The email client will try to render the last part first
   message.attach(part1)
   message.attach(part2)
   if ip_switch_1 != "0":
     message.attach(part3)
   if ip_switch_2 != "0":
      message.attach(part4)
   if re.search("A Pattern has been detected in switch",subject) :
      message.attach(part5)
      message.attach(part6)

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

