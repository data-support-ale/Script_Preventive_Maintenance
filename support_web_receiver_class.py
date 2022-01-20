#!/usr/bin/env python

from flask import Flask, redirect, url_for, request
from time import sleep
import time
import threading
import requests
import sys


class Receiver():

   """ 
   Receiver class permit to collect which choice was chosen and use it in other scripts.
   """

   def __init__(self):
      self.answer = "Not received"

   def get_answer(self):
      return self.answer

   def set_answer(self,answer):
      self.answer = answer




def start_web(receiver,id_client,id_case):
      """ 
      This function start the web server .
      :param Receiver receiver:       The receiver is needed to use the answer from the url link
      :param str id_client:           Unique ID creates during the Setup.sh, to identifie the URL request to the good client
      :param str id_case:             Unique ID creates during the response_handler , to identifie the URL request to the good case.
      """

      time_start = time.time()
      web_server = Flask(__name__)
      id = "{0}{1}".format(id_client,id_case)
      print(id)

      def timeout_request_kill(time_start,id_client,id_case):
         """function to answer yes automatically to stop the server."""

         while  int(time.time())-int(time_start) < 60 :
             sleep(5)
         url = "http://127.0.0.1:5200/?id={0}{1}&answer=yes".format(id_client,id_case)
         try:
             response = requests.get(url)
             print(response)
         except requests.exceptions.ConnectionError:
             print("Max retries exceeded when calling URL: " + url)
             sys.exit()
         except requests.exceptions.Timeout:
             print("Request Timeout when calling URL: " + url)
             sys.exit()    
         except requests.exceptions.TooManyRedirects:
             print("Too Many Redirects when calling URL: " + url)
             sys.exit()    
         except requests.exceptions.RequestException:
             print("Request exception when calling URL: " + url)
             sys.exit()    
    
      def shutdown_server():
          """function to stop the web service."""

          func = request.environ.get('werkzeug.server.shutdown')
          if func is None:
               raise RuntimeError('Not running with the Werkzeug Server')
          func()

      @web_server.route('/')
      def query():
          """ Function to get the '/' web page and accept to parameters in the url 'id' and 'answer'.
          Id is the combination of id_client and id_case. Answer can take 3 options : yes, non, save.
          """

          print(request.args.get('id'))
          if id == request.args.get('id'):
             key = request.args.get('answer')
             if key == 'yes':
                 receiver.set_answer('1')
             elif key == 'no':
                 receiver.set_answer('0')
             elif key == 'save':
                 receiver.set_answer('2')
             else:
                 receiver.set_answer('-1') #error: wrong argument answer
             shutdown_server()
             return "We handle your choice : {0}".format(request.args.get('answer'))

          elif request.args.get('id')=='rainbow':
             shutdown_server()
             print('server shutdown')
             return "Answer received from Rainbow"
          else:
             receiver.set_answer('-2') #error: wrong argument ID
             print("Wrong arguement id")
             return "Wrong argument, please check if this is the last link sent".format(request.args.get('answer'))

      #if __name__ == '__main__':
      #run app in debug mode on port 5000

      #creation timer thread 
      timer = threading.Thread(target=timeout_request_kill, args=(time_start, id_client, id_case))
      #launch timer
      timer.start()
      web_server.run(debug=False, port=5200,host="0.0.0.0")




