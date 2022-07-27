from urllib import request
import requests
import time
import shelve
import os
import logging

def log_module(request,msg,logger):
    print(msg, request)
    msg="userid:"+str(request.user)+" "+msg
    logger.info(msg)

def log_error_module(request,msg,logger):
    msg="userid:"+str(request.user)+" "+msg
    logger.error(msg)

def log_warning_module(request,msg,logger):
    msg="userid:"+str(request.user)+" "+msg
    logger.warn(msg)

def log_module_script(msg):
    path=os.path.dirname(os.path.dirname(__file__))
    logfile=path+"/timelog.log"
    logging.basicConfig(filename=logfile, level=logging.DEBUG)
    logging.info(msg)

def log_error_module_script(msg):
    path=os.path.dirname(os.path.dirname(__file__))
    logfile=path+"/timelog.log"
    logging.basicConfig(filename=logfile, level=logging.DEBUG)
    logging.error(msg)

def log_warning_module_script(msg):
    path=os.path.dirname(os.path.dirname(__file__))
    logfile=path+"/timelog.log"
    logging.basicConfig(filename=logfile, level=logging.DEBUG)
    logging.warning(msg)

def rsyslog_script_timeout(requestdetails,ipencountertime):
    f=shelve.open("iptimelapse")
    if requestdetails in f.keys():
        if(ipencountertime-f[requestdetails])/60<5:
            flag=0
        else:
            f[requestdetails]=ipencountertime
            flag=1
    else:
        f[requestdetails]=ipencountertime
        flag=1
    for key in f.keys():
        if (time.time()-f[key])/60>5:
            f.pop(key)
    f.close()
    if flag==0:
        return True
    else:
        return False
