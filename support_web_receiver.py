#!/usr/bin/env python3

from flask import Flask, redirect, url_for, request
from time import sleep
web_server = Flask(__name__)

def start_web(id):
   def shutdown_server():
       func = request.environ.get('werkzeug.server.shutdown')
       if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
       func()


   @web_server.route('/')
   def query():
       print(request.args.get('id'))
       if id == request.args.get('id'):
          shutdown_server()
       return(request.args.get('id'))


   if __name__ == '__main__':
      # run app in debug mode on port 5000
      web_server.run(debug=True, port=5200,host="10.130.7.14")


start_web('toto')
