#!/usr/bin/env python

from flask import Flask, redirect, url_for, request
from time import sleep
web_server = Flask(__name__)

def start_web(id):
   #id =  (int(id_client)-int(id_case))
   #id = str("%10d" % id)

   def shutdown_server():
       func = request.environ.get('werkzeug.server.shutdown')
       if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
       func()


   @web_server.route('/')
   def query():
       global answer
       print(request.args.get('id'))
       if id == request.args.get('id'):
         # key = request.args.get('answer')
          key = 'yes'
          if key == 'yes':
              answer = 1
          elif key == 'no':
              answer = 0
          elif key == 'save':
              answer = 2
          else:
              answer = -1 #error: wrong argument answer
          shutdown_server()
          return request.args.get('id')

       else:
          answer = -2 #error: wrong argument ID
          print("Wrong arguement id")
       return request.args.get('id')

   if __name__ == '__main__':
      # run app in debug mode on port 5000
      web_server.run(debug=True, port=5200,host="10.130.7.14")


start_web('toto')
id_client = "0123456789"
id_case = "0012345678"

