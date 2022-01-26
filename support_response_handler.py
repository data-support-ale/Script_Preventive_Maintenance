#!/usr/bin/env python
from support_web_receiver_class import Receiver,start_web
from support_send_notification import send_message_request
from support_tools_OmniSwitch import check_save, add_new_save
import threading
import random


def request_handler_rainbow(ip_switch_1,ip_switch_2,port_switch_1,port_switch_2,info,jid,ip_server,id_client,type):
  """ This function is a conductor to handle the url request by Rainbow (send the mail, create the id_case ,save the choice ,start web server,...).

  :param str ip_switch_1:         IP Address of the 1st device concerned by the issue.
  :param str ip_switch_2:         IP Address of the 2nd device concerned by the issue. Equal 0 if empty.
  :param str port_switch_1:       Port number  of the 1st device concerned by the issue.
  :param str port_switch_2:       Port number  of the 2nd device concerned by the issue. Equal 0 if empty.
  :param str info:                Message to send to the rainbow bot
  :param str jid:                 Rainbow JID  of recipients
  :param str ip_server:           IP Adress of the server log , which is also a web server
  :param str id_client:           Unique ID creates during the Setup.sh, to identifie the URL request to the good client
  :param str id_case:             Unique ID creates during the response_handler , to identifie the URL request to the good case.
  """
  if check_save(ip_switch_1,port_switch_1,type) == '0':
     receiver = Receiver()
     id_case = random.randrange(1000000000,9999999999)
     thread_web = threading.Thread(target=start_web, args=(receiver, id_client, id_case))
     thread_web.start()

     send_message_request(info,jid,receiver)
     thread_web.join()
     print(receiver.get_answer())
     #save new state:
     if receiver.get_answer()=='2':
        add_new_save(ip_switch_1,port_switch_1,type,"always")
        if ip_switch_2 != "0":
           add_new_save(ip_switch_2,port_switch_2,type,"always")
        return '1'
     elif receiver.get_answer()=='0':
        add_new_save(ip_switch_1,port_switch_1,type,"never")
        if ip_switch_2 != "0":
           add_new_save(ip_switch_2,port_switch_2,type,"never")
        return '0'
     else:
        return receiver.get_answer()


  elif  check_save(ip_switch_1,port_switch_1,type) == '1':
     return '1'
  elif  check_save(ip_switch_1,port_switch_1,type) == '-1':
     return '0'
