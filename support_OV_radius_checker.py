#!/usr/bin/python
import requests, json
import os
import datetime
import sys
import re
import configparser
import mimetypes
import smtplib
from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from time import gmtime, strftime, localtime, sleep, time
import paramiko




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
  logfilename = "/Log-" + strftime('%Y-%m-%d', localtime(time()))
  path = os.getcwd()
  print(log)
  with open(path + logfilename, "a") as file:
     file.write("{0}: {1}\n".format(datetime.datetime.now(),log))


path = os.getcwd() #get the full path of the  working directory
cp = configparser.ConfigParser()
try:
   configfile = os.path.join(path,'OV_radius_checker.conf')
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

   IP = cp.get('Information', 'IP/URL')
except:
   info = "Error when collecting credentials information in conf file.(One element or more is missing.)\nCompare with the file structure : {0}".format(struct_conf)
   entry_log(info)
   sys.exit()

if User == "" or Pass == "" or IP == "":
   info = "Error when collecting credentials information in conf file.(One element or more is empty.)"
   entry_log(info)
   sys.exit()


try:
   threshold_total = cp.get('Threshold', 'Thresold_All')
   threshold_guest = cp.get('Threshold', 'Thresold_Guest')
   threshold_byod = cp.get('Threshold', 'Thresold_BYOD')
   threshold_employee = cp.get('Threshold', 'Thresold_Employee')
   threshold_unknown = cp.get('Threshold', 'Thresold_Unknown')
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
        url = "https://"+ IP + ":443/api/"
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
        except ValueError:
            return {}

    def get( self, path ):
        r = requests.get( self.ov + path,
                          cookies=self.cookies,
                          verify=False,
                          headers={ 'content-type': 'application/json' } )

        try:
            info = "The get server response : \n {0} \n ".format(r.text)
            entry_log(info)
            return json.loads( r.text )
        except ValueError:
            print ("Exception")
            return {}

    
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



def send_message(info,jid):
    """
    Send the message in info to a Rainbowbot. This bot will send this message to the jid in parameters
    :param str info:                Message to send to the rainbow bot
    :param str jid:                 Rainbow jid where the message will be send
    :return:                        None
    """


    url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif/"
    headers = {'Content-type': 'application/json', "Accept-Charset": "UTF-8", 'jid1': '{0}'.format(jid), 'toto': '{0}'.format(info),'Card': '0'}
    response = requests.get(url, headers=headers)

def send_mail(info,subject,mail_user,mail_password,mails,mail_server,port_server):
  runtime = strftime("%d_%b_%Y_%H_%M_%S_", localtime())

  for mail in mails:
   #email account properties
   #email properties
   sent_from = mail_user
   to = mail

   ### Ajout support MIME
   message = MIMEMultipart("alternative")
   message["Subject"] = "{0}".format(subject)
   message["From"] = sent_from
   message["To"] = to

   email_text = """\
   
      Hello
   This email to notify {0}.""".format(info)


   email_html = """\
   <html>
     <body>
       <p>
       <br>   Hello </br>
          This email to notify {0}.
       </p>
<table class=Tabellanormale border=0 cellpadding=0 align=left width=100 style='width:75.0pt'><tr><td style='border:none;border-top:solid #6B489D 4.5pt;padding:.75pt .75pt .75pt .75pt'></td></tr></table><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 width="100%" style='width:100.0%;background:white'><tr><td valign=top style='padding:0cm 0cm 0cm 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 width="100%" style='width:100.0%'><tr><td valign=top style='padding:11.25pt 0cm 11.25pt 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 width="100%" style='width:100.0%'><tr><td valign=top style='padding:0cm 0cm 0cm 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 width="100%" style='width:100.0%'><tr><td valign=top style='padding:0cm 0cm 0cm 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 align=left width=420 style='width:315.0pt'><tr><td valign=top style='padding:0cm 0cm 0cm 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 align=left><tr><td style='padding:0cm 0cm 0cm 0cm'><p class=MsoNormal><b><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#6B489D'>NBD Support Team<o:p></o:p></span></b></p></td></tr><tr><td style='padding:0cm 0cm 7.5pt 0cm'><p class=MsoNormal style='line-height:13.5pt'><span style='font-size:10.0pt;font-family:ClanOT-Book;color:black'>Alcatel-Lucent Enterprise <o:p></o:p></span></p></td></tr><tr><td style='padding:0cm 0cm 7.5pt 0cm'><p class=MsoNormal><span style='font-size:10.0pt;font-family:ClanOT-Book;color:black'><o:p></o:p></span></p><p class=MsoNormal><span style='font-size:10.0pt;font-family:ClanOT-Book;color:black'><o:p>&nbsp;</o:p></span></p><p class=MsoNormal><b><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#6B489D'><a href="https://web.openrainbow.com/" target="_blank"><span style='color:#6B489D;border:none windowtext 1.0pt;padding:0cm'>Rainbow collaboration platform</span><span style='color:#6B489D;border:none windowtext 1.0pt;padding:0cm;font-weight:normal'> </span></a><o:p></o:p></span></b></p></td></tr><tr><td style='padding:0cm 0cm 0cm 0cm'><p class=MsoNormal style='line-height:13.5pt'><span style='font-size:10.0pt;font-family:ClanOT-Book;color:black'>ALE International <o:p></o:p></span></p></td></tr><tr><td style='padding:0cm 0cm 0cm 0cm'><p class=MsoNormal style='line-height:13.5pt'><span lang=FR style='font-size:10.0pt;font-family:ClanOT-Book;color:black'>115-225 rue A. de St-Exupery<o:p></o:p></span></p><p class=MsoNormal style='line-height:13.5pt'><span lang=FR style='font-size:10.0pt;font-family:ClanOT-Book;color:black'>ZAC Prat Pip - Guipavas<o:p></o:p></span></p></td></tr><tr style='height:60.9pt'><td style='padding:0cm 0cm 7.5pt 0cm;height:60.9pt'><p class=MsoNormal style='line-height:13.5pt'><span style='font-size:10.0pt;font-family:ClanOT-Book;color:black'>29806 BREST, France</span><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#3A3A3A'> <o:p></o:p></span></p><p class=MsoNormal style='line-height:13.5pt'><span style='font-size:10.0pt'><a href="https://www.al-enterprise.com/"><span style='font-family:ClanOT-Book;color:#3A3A3A;text-decoration:none'><img border=0 width=173 height=76 style='width:1.802in;height:.7916in' id="Picture_x0020_1" src="cid:image009.png@01D72707.92BFB2D0" alt="https://www.al-enterprise.com/-/media/assets/internet/images/h-to-m/logo-389x170.png"></span></a></span><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#3A3A3A'><o:p></o:p></span></p><p class=MsoNormal style='line-height:13.5pt'><span style='font-size:10.0pt'><a href="https://www.linkedin.com/company/alcatellucententerprise/"><span style='font-family:ClanOT-Book;color:#3A3A3A;text-decoration:none'><img border=0 width=30 height=30 style='width:.3125in;height:.3125in' id="Picture_x0020_39" src="cid:image010.png@01D72707.92BFB2D0" alt="https://www.al-enterprise.com/-/media/assets/internet/images/h-to-m/in-1080x1080.png"></span></a></span><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#3A3A3A'> </span><span style='font-size:10.0pt'><a href="https://twitter.com/ALUEnterprise"><span style='font-family:ClanOT-Book;color:#3A3A3A;text-decoration:none'><img border=0 width=30 height=30 style='width:.3125in;height:.3125in' id="Picture_x0020_40" src="cid:image011.png@01D72707.92BFB2D0" alt="https://www.al-enterprise.com/-/media/assets/internet/images/t-to-z/tw-1080x1080.png"></span></a></span><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#3A3A3A'> </span><span style='font-size:10.0pt'><a href="https://www.facebook.com/ALUEnterprise"><span style='font-family:ClanOT-Book;color:#3A3A3A;text-decoration:none'><img border=0 width=30 height=30 style='width:.3125in;height:.3125in' id="Picture_x0020_41" src="cid:image012.png@01D72707.92BFB2D0" alt="https://www.al-enterprise.com/-/media/assets/internet/images/a-to-g/fb-1080x1080.png"></span></a></span><span style='font-size:10.0pt;font-family:ClanOT-Book;color:#3A3A3A'><o:p></o:p></span></p></td></tr><tr><td style='padding:0cm 0cm 0cm 0cm'></td></tr></table></td></tr></table></td></tr></table></td></tr><tr><td valign=top style='padding:0cm 0cm 0cm 0cm'><table class=Tabellanormale border=0 cellspacing=0 cellpadding=0 width="100%" style='width:100.0%'><tr><td valign=top style='padding:3.75pt 0cm 0cm 0cm'><p class=MsoNormal style='text-align:justify;text-justify:inter-ideograph;line-height:12.0pt'><span style='font-size:7.0pt;font-family:ClanOT-Book;color:#BBBCBC'>The Alcatel-Lucent name and logo are trademarks of Nokia used under license by ALE. <o:p></o:p></span></p><p class=MsoNormal style='text-align:justify;text-justify:inter-ideograph;line-height:12.0pt'><span style='font-size:7.0pt;font-family:ClanOT-Book;color:#BBBCBC'>This communication is intended to be received only by the individual or entity to whom or to which it is addressed and may contain information that is privileged, is confidential and is subject to copyright. Any unauthorized use, copying, review or disclosure of this communication is strictly prohibited. If you have received this communication in error, please delete this message from your email box and information system (including all files and documents attached) and notify the sender by reply email. Please consider protecting the environment before printing. Thank you for your cooperation.</span><span style='font-size:7.0pt;font-family:ClanOT-Book;color:#B8B8B8'> </span><span style='font-size:8.5pt;font-family:ClanOT-Book;color:#B8B8B8'><o:p></o:p></span></p></td></tr></table></td></tr></table></td></tr></table></td></tr></table><p class=MsoNormal><o:p>&nbsp;</o:p></p><p class=MsoNormal><o:p>&nbsp;</o:p></p></div>
     </body>
   </html>   """.format(info)

   # Turn these into plain/html MIMEText objects
   part1 = MIMEText(email_text, "plain")
   part2 = MIMEText(email_html, "html")
   message.attach(part1)
   message.attach(part2)


   # Add HTML/plain-text parts to MIMEMultipart message
   # The email client will try to render the last part first
 
   #email send request
   try:
       server = smtplib.SMTP_SSL(mail_server, port_server)
       server.ehlo()
       server.login(mail_user, mail_password)
       server.sendmail(sent_from, to, message.as_string())
       server.close()
       info = runtime + 'Email sent!'
       entry_log(info)
       #logging.debug(runtime + 'Email sent!')
   except Exception as e:
       info =  'Error when sending email : \n {0} \n'.format(e)
       entry_log(info)

def restart_freeradius_service():
       ssh = createSSHClient(IP, "2222", User_root, Password_root)

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


    if value_total < int(threshold_total):
       info= "Number of Total Active Radius Authentication : {0} is under than fixed Threshold : {1}".format(value_total,threshold_total)
       subject = "Number of Total Active Radius Authentication is under than fixed Threshold, Radius service has been restarted"
       entry_log(info)
       restart_freeradius_service()
       if email_notif==1:
          send_mail(info,subject,mail_user,mail_password,mails,mail_server,port_server)
       if jid_notif==1:
          send_message(info,jid)

    elif value_employee < int(threshold_employee):
       info="Number of Employee Active Radius Authentication : {0} is under than fixed Threshold : {1}".format(value_employee,threshold_employee)
       subject = "Number of Employee Active Radius Authentication is under than fixed Threshold, Radius service has been restarted"

       restart_freeradius_service()

       entry_log(info)
       if email_notif==1:
          send_mail(info,subject,mail_user,mail_password,mails,mail_server,port_server)
       if jid_notif==1:
          send_message(info,jid)
    elif value_byod < int(threshold_byod):
       info="Number of BYOD Active Radius Authentication : {0} is under than fixed Threshold : {1}".format(value_byod,threshold_byod)
       subject = "Number of BYOD Active Radius Authentication is under than fixed Threshold, Radius service has been restarted"

       restart_freeradius_service()

       entry_log(info)
       if email_notif==1:
          send_mail(info,subject,mail_user,mail_password,mails,mail_server,port_server)
       if jid_notif==1:
          send_message(info,jid)
    elif value_guest < int(threshold_guest):
       info="Number of Guest Active Radius Authentication : {0} is under than fixed Threshold : {1}".format(value_guest,Thresold_Guest)
       subject = "Number of Guest Active Radius Authentication is under than fixed Threshold, Radius service has been restarted"
      
       restart_freeradius_service()

       entry_log(info) 
       if email_notif==1:
          send_mail(info,subject,mail_user,mail_password,mails,mail_server,port_server)
       if jid_notif==1:
          send_message(info,jid)
    elif value_unknown < int(threshold_unknown):
       info="Number of Unknown Active Radius Authentication : {0} is under than fixed Threshold : {1}".format(value_unknown,Thresold_Unknown)
       subject = "Number of Unknown Active Radius Authentication is under than fixed Threshold, Radius service has been restarted"

       restart_freeradius_service()

       entry_log(info)
       if email_notif==1:
          send_mail(info,subject,mail_user,mail_password,mails,mail_server,port_server)
       if jid_notif==1:
          send_message(info,jid)


while True:
   try:
      main()
   except Exception as e:
      info = "Error when collecting Radius data : \n {0} ".format(e)   
      entry_log(info)
   sleep(60)
