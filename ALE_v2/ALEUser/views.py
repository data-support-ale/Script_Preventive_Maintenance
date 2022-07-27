
from django.views.decorators.csrf import csrf_exempt
from io import DEFAULT_BUFFER_SIZE
from ipaddress import ip_address
from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import *
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from rest_framework import permissions
from rest_framework.authtoken.serializers import AuthTokenSerializer
from .models import *
from rest_framework import status
from itertools import groupby
from datetime import date
import re
import json
import requests
import logging,traceback
import uuid
import socket
import platform
import os
import psutil
import math
from requests.exceptions import ConnectionError
#from django.views.decorators.csrf import csrf_exempt
import pyufw as ufw
import os
from django.http import FileResponse
from alelog import alelog
import zipfile
import pandas as pd
import glob
from pathlib import Path
import shutil
import subprocess

logger=logging.getLogger('alelog')
@api_view(['GET'])
def index(request):
    url_list={
        # login & logout 
        "login" : "127.0.0.1:8000/api/login",
        "logout" : "127.0.0.1:8000/api/logout",

        # users 
        "User - View or Register" : "127.0.0.1:8000/api/users/",
        "User - Modify, Delete, Password Update" : "127.0.0.1:8000/api/users/<id>/",
        
        #decision 
        "Decision create" : "27.0.0.1:8000/api/decisioncreate - disabled",
        "Decision List" : "127.0.0.1:8000/api/decisions",
        "Decision delete" : "127.0.0.1:8000/api/decisions/<id>",
        "Decision Filter" : "127.0.0.1:8000/api/decisions/decisionfilter",
        
        #rules 
        "Rules Create" : "127.0.0.1:8000/api/rules",
        "Rules List" : "127.0.0.1:8000/api/rules",
        "Rules Delete" : "127.0.0.1:8000/api/rules/<id>",
        "Rules Edit" : "127.0.0.1:8000/api/rules/<id>",
        "Rules Enable" : "127.0.0.1:8000/api/rules/enable",
        
        #statistics 
        "Statistics List" : "127.0.0.1:8000/api/statistics",
        "Statistics Filter" : "127.0.0.1:8000/api/statistics/datafilter",
        
        #settings 
        "Settings - View or Update" : "127.0.0.1:8000/api/settings/",
        "About ": "127.0.0.1:8000/api/about",
        "Log Download": "127.0.0.1:8000/api/download",
		"Settings - Test Connection" : "127.0.0.1:8000/api/testconnection/",

        #upload scripts offline
        "Upload Script Offline" : "127.0.0.1:8000/api/upload-offline/",

        "Profile view/edit": "127.0.0.1:8000/api/profile",

        #upgarde from ale repository
        "Upload from ALE Repository" : "127.0.0.1:8000/api/ale-upgrade/"
    }
    alelog.log_module(request,"URL list page visited",logger)
    return Response(url_list)

################
## User API's ##
################

@api_view(['POST'])
def UserLogin(request):
    print(request.user.is_authenticated)
    if request.user.is_authenticated==False:
        data=request.data
        username_email=data.get('username','')
        password=data.get('password','')
        username=username_email
        if '@' in username_email:
            try:
                loginuser=Users.objects.get(email=username_email)
                print(loginuser)
            except Users.DoesNotExist:
               message={"Status":"Failure","Message":"Invalid Username or Password","Code":"400"}
               alelog.log_error_module(request,"Invalid Username or password",logger)
               return Response(message,status=400)
            username=User.objects.get(id=loginuser.user_name.id).username
        user=authenticate(request,username=username,password=password)
        if user is not None:
            login(request,user)
            ser1=Users.objects.get(user_name=user.id)
            ser=UserTypesSerializer(ser1.type_id,many=False)
            alelog.log_module(request,"Login Success",logger)
            message={"Status":"Success","Message":"Login Successful","Code":"200","user_id":user.id,"user_email":username_email,"user_name":username}
            message.update(ser.data)
            return Response(message)
        alelog.log_error_module(request,"Invalid Username or password",logger)
        message={"Status":"Failure","Message":"Invalid Username or Password","Code":"400",}
        return Response(message,status=400)
    alelog.log_warning_module(request,"Already logged In",logger)
    return Response("Already logged in",status=400)


@api_view(['GET'])
def UserLogout(request):
    if request.user.is_authenticated==False:
        alelog.log_warning_module(request,"No user logged in",logger)
        return Response({"Status":"Failed","Message":"No login user","Code":"400"},status=400)
    alelog.log_module(request,"Logout Success",logger)
    logout(request)
    return Response({"Status":"Success","Message":"Logout Successful","Code":"200"})

def ViewUsers(request):
    #    This function is used for the viewing of all the user.
    if request.user.is_anonymous == True:
        message = {
            "Status": "Failure",
            "Message": "User not logged in", 
            "Code": "400"
        }
        alelog.log_warning_module(request,"No user logged in",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)
    user = Users.objects.get(user_name = request.user)
    if user.type_id.type_name == 'regular':
        message = {
			"Status": "Failure",
			"Message": "Insufficient Permission",
			"Code": "401"
		}
        alelog.log_error_module(request,"Insufficient permission",logger)
        return Response(message, status=status.HTTP_401_UNAUTHORIZED)
    try: 
        users = Users.objects.all()
        users_list = UserDetails(users, many=True)
        message = {
			"Status": "Success",
			"Message": "Users List",
			"Code": "200",
			"All_Users": users_list.data
		}
        alelog.log_module(request,"User list viewed",logger)
        return Response(message, status=status.HTTP_200_OK)
    except Exception as exception:
        message = {
			"Status": "Failure",
			"Message": "No User Present",
			"Code": "400",
			"Error Message": exception.args
		}
        alelog.log_warning_module(request,"No users present",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

def UserRegistration(request):
    """
        This function is used for the creation of the user.
    """

    if request.user.is_anonymous == True:
        message = {
            "Status": "Failure",
            "Message": "User not logged in", 
            "Code": "400"
        }
        alelog.log_warning_module(request,"No user logged in",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

    user = Users.objects.get(user_name = request.user)
    if user.type_id.type_name == 'regular':
        message = {
            "Status": "Failure",
            "Message": "Insufficient Permission",
            "Code": "401"
        }
        alelog.log_warning_module(request,"Insufficient Permission",logger)
        return Response(message, status=status.HTTP_401_UNAUTHORIZED)

    try:
        user_type_serializer = CustomUserTypeSerializer(data=request.data)
        default_serializer = UserRegistrationSerializer(data=request.data)
        custom_serializer = CustomUserRegistrationSerializer(data=request.data)

        if user_type_serializer.is_valid() and default_serializer.is_valid() and custom_serializer.is_valid():
            user_type = user_type_serializer.save()
            default_user = default_serializer.save()
            custom_user = custom_serializer.save()

            custom_user.type_id = user_type
            custom_user.user_name = default_user
            custom_user.save()

            message = {
                "Status": "Success",
                "Message": "User Created",
                "Code": "201",
                "Created_User": {
                    "username": custom_user.user_name.username,
                    "email ID": custom_user.email,
                    "user type": custom_user.type_id.type_name,
                    "jid": custom_user.jid
                }
            }
            alelog.log_module(request,"New User Created",logger)
            return Response(message, status=status.HTTP_201_CREATED)

        message = {
            "Status": "Failure",
            "Message": "User Creation Failed",
            "Code": "400",
            "Error Message": default_serializer.errors
        }
        alelog.log_error_module(request,"New User creation failed",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

    except Exception as exception:
        message = {
            "Status": "Failure",
            "Message": "User Creation Failed",
            "Code": "400",
            "Error Message": exception.args
        }
        default_user.delete()
        alelog.log_error_module(request,"user Creation failed",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
def UserFunctionDistributor(request):
    if request.method == 'GET':
        return ViewUsers(request)
    
    elif request.method == 'POST':
        return UserRegistration(request)

@api_view(['DELETE'])
def UserDeletion(request, user_id):
    """
        This function is used for the deletion of the user.

        :param int user_id: User's primary key
    """

    if request.user.is_anonymous == True:
        message = {
            "Status": "Failure",
            "Message": "User not logged in", 
            "Code": "400"
        }
        alelog.log_warning_module(request,"No user logged in",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

    user = Users.objects.get(user_name = request.user)
    if user.type_id.type_name == 'regular':
        message = {
            "Status": "Failure",
            "Message": "Insufficient Permission",
            "Code": "401"
        }
        alelog.log_warning_module(request,"Insufficient Permission",logger)
        return Response(message, status=status.HTTP_401_UNAUTHORIZED)

    try:
        user = Users.objects.get(user_id=user_id)

        # deleting the user from django user table
        User.objects.get(username=user.user_name).delete()

        user.delete()
        message = {
            "Status": "Success",
            "Message": "User Deleted",
            "Code": "200",
            "Deleted_User": {
                "username": user.user_name.username,
                "email ID": user.email,
                "user type": user.type_id.type_name
            }
        }
        alelog.log_module(request,"User Deleted",logger)
        return Response(message, status=status.HTTP_200_OK)

    except Users.DoesNotExist:
        message = {
            "Status": "Failure",
            "Message": "User doesn't exist",
            "Code": "404"
        }
        alelog.log_error_module(request,"User Dont Exist",logger)
        return Response(message, status=status.HTTP_404_NOT_FOUND)

    except Exception as exception:
        message = {
            "Status": "Failure",
            "Message": "User Deletion Failed",
            "Code": "400",
            "Error Message": exception.args
        }
        alelog.log_error_module(request,"User Deletion Failed",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def UserEdition(request, user_id):
    """
        This function is used for the updation of the user.

        :param int user_id: User's primary key
    """

    if request.user.is_anonymous == True:
        message = {
            "Status": "Failure",
            "Message": "User not logged in", 
            "Code": "400"
        }
        alelog.log_warning_module(request,"No user logged in",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

    user = Users.objects.get(user_name = request.user)
    if user.type_id.type_name == 'regular':
        message = {
            "Status": "Failure",
            "Message": "Insufficient Permission",
            "Code": "401"
        }
        alelog.log_warning_module(request,"Insufficient Permission",logger)
        return Response(message, status=status.HTTP_401_UNAUTHORIZED)

    try:
        custom_user = Users.objects.get(user_id=user_id)
        default_user = User.objects.get(username=custom_user.user_name)

        user_type_serializer = CustomUserTypeSerializer(data=request.data)
        default_serializer = UserRegistrationSerializer(instance=default_user, data=request.data)
        custom_serializer = CustomUserRegistrationSerializer(instance=custom_user, data=request.data)

        lower_email = custom_serializer.initial_data['email'].lower()
        if custom_user.email != lower_email and Users.objects.filter(email__iexact=lower_email).exists():
            raise serializers.ValidationError("Duplicate Email")

        if user_type_serializer.is_valid() and default_serializer.is_valid() and custom_serializer.is_valid():
            user_type = user_type_serializer.save()
            default_user = default_serializer.save()
            custom_user = custom_serializer.save()

            default_user.set_password(request.data['password'])
            default_user.save()

            custom_user.email = lower_email
            custom_user.type_id = user_type
            custom_user.user_name = default_user
            custom_user.save()

            message = {
                "Status": "Success",
                "Message": "User Updated",
                "Code": "200",
                "Updated_User": {
                    "username": custom_user.user_name.username,
                    "email ID": custom_user.email,
                    "user type": custom_user.type_id.type_name,
                    "jid": custom_user.jid
                }
            }
            alelog.log_module(request,"User data updated",logger)
            return Response(message, status=status.HTTP_200_OK)

        message = {
            "Status": "Failure",
            "Message": "User Updation Failed",
            "Code": "400",
            "Error Message": default_serializer.errors
        }
        alelog.log_error_module(request,"User updation failed",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

    except Users.DoesNotExist:
        message = {
            "Status": "Failure",
            "Message": "User doesn't exist",
            "Code": "404"
        }
        alelog.log_error_module(request,"user Dont Exist",logger)
        return Response(message, status=status.HTTP_404_NOT_FOUND)

    except Exception as exception:
        message = {
            "Status": "Failure",
            "Message": "User Updation Failed",
            "Code": "400",
            "Error Message": exception.args
        }
        alelog.log_error_module(request,"User updation failed",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def UpdatePassword(request, user_id):
    """
        This function is used for the updation of the user's password.

        :param int user_id: User's primary key
    """

    if request.user.is_anonymous == True:
        message = {
            "Status": "Failure",
            "Message": "User not logged in", 
            "Code": "400"
        }
        alelog.log_warning_module(request,"No user logged in",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

    user = Users.objects.get(user_name = request.user)
    if user.type_id.type_name == 'regular':
        message = {
            "Status": "Failure",
            "Message": "Insufficient Permission",
            "Code": "401"
        }
        alelog.log_warning_module(request,"Insufficient Permission",logger)
        return Response(message, status=status.HTTP_401_UNAUTHORIZED)

    try:
        custom_user = Users.objects.get(user_id=user_id)
        default_user = User.objects.get(username=custom_user.user_name)

        if request.data['new_password'] and request.data['new_password_confirmation'] and request.data['new_password'] == request.data['new_password_confirmation']:
            default_user.set_password(request.data['new_password'])
            default_user.save()
            message = {
                "Status": "Success",
                "Message": "Password Updated",
                "Code": "200"
            }
            alelog.log_module(request,"Password updated for user",logger)
            return Response(message, status=status.HTTP_200_OK)

        else:
            message = {
                "Status": "Failure",
                "Message": "Password and Password-Confirmation are not same",
                "Code": "400"
            }
            alelog.log_error_module(request,"Password and confirm password are not same",logger)
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

    except Users.DoesNotExist:
        message = {
            "Status": "Failure",
            "Message": "User doesn't exist",
            "Code": "404"
        }
        alelog.log_error_module(request,"User Dont exist",logger)
        return Response(message, status=status.HTTP_404_NOT_FOUND)

    except Exception as exception:
        message = {
            "Status": "Failure",
            "Message": "Password Updation Failure",
            "Code": "400",
            "Error Message": exception.args
        }
        alelog.log_error_module(request,"Password Updation Failed",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'DELETE'])
def ModifyUserFunctionDistributor(request, user_id):      
    if request.method == 'DELETE':
        return UserDeletion(request._request, user_id)

    elif request.method == 'PUT':
        received_json_data = json.loads(request.body.decode("utf-8"))
        received_json_data_length = len(received_json_data)

        if received_json_data_length == 5:
            return UserEdition(request._request, user_id)
        
        elif received_json_data_length == 2:
            return UpdatePassword(request._request, user_id)

# Decision history/ decision list, delete, filter and create apis as follows

@api_view(['GET'])
def DecisionList(request):
    if request.user.is_authenticated==True:
        decision_history=Decision_History.objects.all()
        print(decision_history)
        ser=DecisionListSerializer(decision_history,many=True)
        print(ser.data)
        message={"Status":"Success","Message":"Success","Code":"200",'Decision':ser.data}
        alelog.log_module(request,"Decision History list viewed",logger)
        return Response(message)
    message = {"Status": "Failure","Message": "User not logged in. Need to login to view this page", "Code": "400"}
    alelog.log_warning_module(request,"No user logged in",logger)
    return Response(message, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def DecisionDelete(request,pk):
    if request.user.is_authenticated==True:
        user = Users.objects.get(user_name = request.user)
        if user.type_id.type_name == 'regular':
            alelog.log_warning_module(request,"Insufficient Permission",logger)
            return Response({"Status": "Failure","Message": "Insufficient Permission","Code": "401"}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            decision_history=Decision_History.objects.get(id=pk)
            ser=DecisionListSerializer(decision_history,many=False)
            print(ser.data)
            message={"Status":"Success","Message":"Deleted Decision","Code":"200","deleted_decision":ser.data}
            decision_history.delete()
            alelog.log_module(request,"Decision History deleted",logger)
            return Response(message)
        except Decision_History.DoesNotExist:
            alelog.log_error_module(request,"Decision dont exist",logger)
            message = {"Status": "Failure","Message": "Decision doesn't exist","Code": "404"}
            return Response(message, status=status.HTTP_404_NOT_FOUND)
        except Exception as exception:
            message = {"Status": "Failure","Message": "Decision Deletion Failed","Code": "400","Error Message": exception.args}
            alelog.log_error_module(request,"Decision History Deletion failed",logger)
            return Response(message, status=status.HTTP_400_BAD_REQUEST)
    message = {"Status": "Failure","Message": "User not logged in. Need to login to view this page", "Code": "400"}
    alelog.log_warning_module(request,"No user logged in",logger)
    return Response(message, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def DecisionFilter(request):
    if request.user.is_authenticated==True:
        user = Users.objects.get(user_name = request.user)
        if user.type_id.type_name == 'regular':
            alelog.log_warning_module(request,"Insufficient Permission",logger)
            return Response({"Status": "Failure","Message": "Insufficient Permission","Code": "401"}, status=status.HTTP_401_UNAUTHORIZED)
        ip_address=request.data.get('ip_address','')
        regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
        if(re.search(regex, ip_address)):
            try:
                decision_history=Decision_History.objects.filter(ip_address=ip_address)
                message={"Status":"Success","Message":"Success","Code":"200"}
                '''decisionlist=[]
                for i in decision_history:
                    var={}
                    var['ip_address']=i.ip_address
                    var['port']=i.port
                    var['functions']=Rules.objects.get(rules_id=i.rule_id.rules_id).rule_name
                    var['decision']=i.decision.decision
                    decisionlist.append(var)
                if decisionlist==[]:
                    decisionlist="No list exist"
                message['decision']=decisionlist'''
                ser=DecisionListSerializer(decision_history,many=True)
                if ser.data==[]:
                    message={"Status":"Success","Message":"No data","Code":"200","decision":"No data"}
                else:
                    message={"Status":"Success","Message":"success","Code":"200","decision":ser.data}
                alelog.log_module(request,"Decision filter search",logger)
                return Response(message)
            except Decision_History.DoesNotExist:
                message = {"Status": "Failure","Message": "Decision doesn't exist","Code": "404"}
                alelog.log_error_module(request,"Decision dont exist",logger)
                return Response(message, status=status.HTTP_404_NOT_FOUND)
            except Exception as exception:
                message = {"Status": "Failure","Message": "Decision Deletion Failed","Code": "400","Error Message": exception.args}
                alelog.log_error_module(request,"Decision History Deletion Failed",logger)
                return Response(message, status=status.HTTP_400_BAD_REQUEST)
        else:
            message={"Status":"Failure","Message":"Invalid IP format","Code":"400"}
            alelog.log_error_module(request,"Invalid IP format",logger)
            return Response(message, status=400)
    message = {"Status": "Failure","Message": "User not logged in. Need to login to view this page", "Code": "400"}
    alelog.log_warning_module(request,"No user logged in",logger)
    return Response(message, status=status.HTTP_400_BAD_REQUEST)

'''@api_view(['POST'])
def DecisionCreate(request):
    if request.user.is_authenticated==True:
        user = Users.objects.get(user_name = request.user)
        if user.type_id.type_name == 'regular':
            return Response({"Status": "Failure","Message": "Insufficient Permission","Code": "401"}, status=status.HTTP_401_UNAUTHORIZED)
        rulename=request.data.get('rule_name','')
        ipaddress=request.data.get('ip_address','')
        port=request.data.get('port','')
        decision=request.data.get('decision','')
        regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
        if re.search(regex, ipaddress) == None:
            message={"Status":"Failure","Message":"Invalid ip format","Code":"400"}
            return Response(message, status=400)
        try:
            val=int(port)
        except ValueError:
            message={"Status":"Failure","Message":"Invalid port format","Code":"400"}
            return Response(message, status=400)
        try:
            rule=Rules.objects.get(rule_name=rulename)
        except Rules.DoesNotExist:
            message={"Status":"Failure","Message":"Invalid Rule","Code":"400"}
            return Response(message, status=400)
        try:
            decision=Decision.objects.get(decision=decision)
        except Decision.DoesNotExist:
            message={"Status":"Failure","Message":"Invalid Decision","Code":"400"}
            return Response(message, status=400)
        try:
            decision_history=Decision_History.objects.create(rule_id=rule,ip_address=ipaddress,port=port,decision=decision)
        except Exception as exception:
                message = {"Status": "Failure","Message": "Decision creation Failed","Code": "400","Error Message": exception.args}
        ser=DecisionListSerializer(decision_history,many=False)
        message={"Status":"Success","Message":"Decision created","Code":"200","decision":ser.data}
        return Response(message)
    message = {"Status": "Failure","Message": "User not logged in. Need to login to view this page", "Code": "400"}
    return Response(message, status=status.HTTP_400_BAD_REQUEST)'''

# views for  rules create, delete, edit and filter
def key_func(k):
    return k['rule_type']


# helper function for returing the rulename for rsyslog and databse connectivity
def get_rule_name(a):
    save = ''
    i = 0

    while i < len(a):
        if a[i] == "'" or a[i] == '"':
            i += 1
            while i < len(a) and (a[i] not in [ "'", '"']):
                save += a[i]
                i += 1
            save += ";"
            
        i += 1
    save = save[:-1]
        
    sep = []
    for i in a.split():
        if i in ['and', 'or']:
            sep.append(i)
            
    # print(sep)
    # print(save) 

    str_ = ""
    for i in save.split(";"):
        str_ += i
        if sep:
            str_ += ';'
            str_ += sep.pop(0)
            str_ += ';'
        
    # print(str_)
    return str_


@api_view(['POST','GET'])
def RulesCreateList(request):
    if request.method=='POST':
        if request.user.is_authenticated==True:
            print("Eneted")
            user = Users.objects.get(user_name = request.user)
            if user.type_id.type_name == 'regular':
                alelog.log_warning_module(request,"Insufficient Permission",logger)
                return Response({"Status": "Failure","Message": "Insufficient Permission","Code": "401"}, status=status.HTTP_401_UNAUTHORIZED)
            rulename=request.data.get('rule_name','')
            action=request.data.get('action','')
            ruledescription=request.data.get('description','')
            action_data=0
            try:
                rule=Rules.objects.get(rule_name=rulename)
                message = {
                    "Status": "Failure","Message": "Rule already exist","Code": "400"
                }
                alelog.log_warning_module(request,"Rule already exist",logger)
                return Response(message, status=400)
            except Rules.DoesNotExist:
                try:
                    action_data=Actions.objects.get(action=action)
                    ruletype=RulesTypes.objects.get(type_name='Custom')
                    rules=Rules.objects.create(rule_name=rulename,rule_type_id=ruletype,action_id=action_data,enabled=True,timeout=5,rule_description=ruledescription)
                except Actions.DoesNotExist:
                    action_data=Actions.objects.create(action=action)
                    ruletype=RulesTypes.objects.get(type_name='Custom')
                    rules=Rules.objects.create(rule_name=rulename,rule_type_id=ruletype,action_id=action_data,enabled=True,timeout=5,rule_description=ruledescription)
                print(action_data.action)
                ser=RuleCreateSerializer(rules)
                print(ser.data)
                rule_insert=rulename+" then {\n"
                #"if "+rulename+" then {\n" - rectified f
                path=os.path.dirname(__file__)
                with open(r"/etc/rsyslog.conf", 'r+') as file:
                    lines = file.readlines()
                    file.seek(0)
                    file.truncate()
                    file.writelines(lines[:-2])
                    if lines[-2][0:10]!=":syslogtag":
                        file.write(lines[-2])
                        # file.write(lines[-1])
                    if '& stop' not in lines[-1]:
                        file.write(lines[-1])

                    file.write(rule_insert)
                    file.write("$RepeatedMsgReduction on\n")
                    file.write("action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")\n")
                    file.write("action(type=\"omfile\" DynaFile=\"customlog\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")\n")
                    if action=="Send Notification":
                        rsys_entry="action(type=\"omprog\" name=\"support_switch_custom_rule\" binary=\""+os.path.abspath(os.path.join(path,os.pardir))+"/ale_scripts/support_switch_custom_rule.py \\\"Send Notification\\\" \\\"" + get_rule_name(rulename) + "\\\"\")"
                        file.write(rsys_entry+"\n")
                    elif action=="Increase log verbosity":
                        rsys_entry="action(type=\"omprog\" name=\"support_switch_custom_rule\" binary=\""+os.path.abspath(os.path.join(path,os.pardir))+"/ale_scripts/support_switch_custom_rule.py \\\"Increase log verbosity\\\" \\\"" + get_rule_name(rulename) + "\\\"\")"
                        file.write(rsys_entry+"\n")
                    elif action=="Collect log and send notification":
                        rsys_entry="action(type=\"omprog\" name=\"support_switch_custom_rule\" binary=\""+os.path.abspath(os.path.join(path,os.pardir))+"/ale_scripts/support_switch_custom_rule.py \\\"Collect log and send notification\\\" \\\"" + get_rule_name(rulename) + "\\\"\")"
                        file.write(rsys_entry+"\n")

                    file.write("stop\n")
                    file.write("}\n")
                    file.write(":syslogtag, contains, \"montag\" /var/log/devices/script_execution.log\n")
                    file.write("& stop\n")
                    file.close()
                os.system("systemctl restart rsyslog")
                alelog.log_module(request,"Rule created and updated in rsyslog",logger)
                return Response(ser.data)
        message = {"Status": "Failure","Message": "User not logged in. Need to login to view this page", "Code": "400"}
        alelog.log_warning_module(request,"No user logged in",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)
    elif request.method=='GET':
        if request.user.is_authenticated==True:
            rule_list=Rules.objects.all()
            message={"Status":"Success","Message":"Success","Code":"200"}
            ser=RuleListSerializer(rule_list,many=True)
            #if ser.data==[]:
            #    message.update({"Message":"No List exist"})
            #    return Response(message)
            rulelist={}
            for element in ser.data:
                indexname=element['rule_type']
                del element['rule_type']
                element.update(indexname)
                indexname=element['action']
                del element['action']
                element.update(indexname)
            resultset={"Status":"Success","Message":"Success","Code":"200"}
            resultset['data']=[]
            i=0
            rulelist={}
            val=sorted(ser.data,key=key_func)
            for key, value in groupby(val,key_func):
                rulelist={}
                rulelist['rule_type']=key
                rulelist['rules']=list(value)
                resultset['data'].append(rulelist)
            alelog.log_module(request,"Rule list viewed",logger)
            return Response(resultset)
        message = {"Status": "Failure","Message": "User not logged in. Need to login to view this page", "Code": "400"}
        alelog.log_warning_module(request,"No user logged in",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT','DELETE'])
def RulesDeleteEdit(request,pk):
    if request.user.is_authenticated==True:
        user = Users.objects.get(user_name = request.user)
        if user.type_id.type_name == 'regular':
            alelog.log_warning_module(request,"Insufficient Permission",logger)
            return Response({"Status": "Failure","Message": "Insufficient Permission","Code": "401"}, status=status.HTTP_401_UNAUTHORIZED)
        if request.method=='DELETE':
            try:
                rule=Rules.objects.get(rules_id=pk)
                if rule.rule_type_id.type_name=="Default":
                     alelog.log_error_module(request,"Rule cant be deleted",logger)
                     return Response({"Status": "Failure","Message": "Cant delete Default Rule","Code": "400"}, status=status.HTTP_400_BAD_REQUEST)
            except Rules.DoesNotExist:
                message = {
                    "Status": "Failure","Message": "Rule doesn't exist","Code": "404"
                }
                alelog.log_warning_module(request,"Rule dont exist",logger)
                return Response(message, status=status.HTTP_404_NOT_FOUND)
            action=Actions.objects.get(action_id=rule.action_id.action_id)
            message={"Status":"Success","Message":"Deleted Rule Success","Code":"200"}
            deletedata={}
            deletedata['rule_name']=rule.rule_name
            deletedata['action']=action.action
            deletedata['description']=rule.rule_description
            message['deleted_rule']=deletedata
            rule.delete()
            flg=99
            del_lines=6
            deleted_rule=deletedata['rule_name']+" then {\n"
            #"if "+deletedata['rule_name']+" then {\n"
            with open("/etc/rsyslog.conf","r") as file:
                lines=file.readlines()
            with open("/etc/rsyslog.conf","w") as file:
                for line in lines:
                    if line==deleted_rule:
                        flg=0
                        cnt=1
                    elif flg==0:
                        if cnt<del_lines:
                            cnt=cnt+1
                            continue
                        flg=99
                    else:
                        file.write(line)
                file.close()
            os.system("systemctl restart rsyslog") 
            alelog.log_warning_module(request,"Rule deleted in db and rsyslog",logger)       
            return Response(message)
        elif request.method=='PUT':
            rulename=request.data.get('rule_name','')
            action=request.data.get('action','')
            ruledescription=request.data.get('description','')
            action_data=0
            try:
                rules=Rules.objects.get(rules_id=pk)
                if rules.rule_type_id.type_name=="Default":
                    alelog.log_error_module(request,"Editing Default rule failed",logger)
                    return Response({"Status": "Failure","Message": "Cant edit Default Rule","Code": "400"}, status=status.HTTP_400_BAD_REQUEST)
            except Rules.DoesNotExist:
                message = {
                    "Status": "Failure","Message": "Rule doesn't exist","Code": "404"
                }
                alelog.log_error_module(request,"Rule Dont exist",logger)
                return Response(message, status=status.HTTP_404_NOT_FOUND)
            try:
                action_data=Actions.objects.get(action=action)
                #ruletype=RulesTypes.objects.get(type_name='Custom Rules')
                old_rulename=rules.rule_name
                print(old_rulename)
                rules.rule_name=rulename
                rules.action_id=action_data
                rules.rule_description=ruledescription
            except Actions.DoesNotExist:
                action_data=Actions.objects.create(action=action)
                rules.action_id=action_data
                rules.rule_name=rulename
                rules.rule_description=ruledescription
            rules.save()
            print(action_data.action)
            message={"Status":"Success","Message":"Edit Rule Success","Code":"200"}
            updatedata={}
            updatedata['rule_name']=rulename
            updatedata['action']=action
            updatedata['descrption']=ruledescription  
            updatedata['enabled']=rules.enabled      
            message['edited_rule']=updatedata
            flg=99
            path=os.path.dirname(__file__)
            with open("/etc/rsyslog.conf","r") as file:
                lines=file.readlines()
            with open("/etc/rsyslog.conf","w") as file:
                for line in lines:
                    if line==old_rulename+" then {\n":
                        file.write(rulename+" then {\n")
                        #"if "+rulename+" then {\n")
                        flg=0
                        cnt=0
                    elif flg==0:
                        if cnt==0:
                            #file.write(rule_insert)
                            file.write("$RepeatedMsgReduction on\n")
                            file.write("action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")\n")
                            file.write("action(type=\"omfile\" DynaFile=\"customlog\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")\n")
                            if action=="Send Notification":
                                rsys_entry="action(type=\"omprog\" name=\"support_switch_custom_rule\" binary=\""+os.path.abspath(os.path.join(path,os.pardir))+"/ale_scripts/support_switch_custom_rule.py \\\"Send Notification\\\" \\\"" + get_rule_name(rulename) + "\\\"\")"
                                file.write(rsys_entry+"\n")
                            elif action=="Increase log verbosity":
                                rsys_entry="action(type=\"omprog\" name=\"support_switch_custom_rule\" binary=\""+os.path.abspath(os.path.join(path,os.pardir))+"/ale_scripts/support_switch_custom_rule.py \\\"Increase log verbosity\\\" \\\"" + get_rule_name(rulename) + "\\\"\")"
                                file.write(rsys_entry+"\n")
                            elif action=="Collect log and send notification":
                                rsys_entry="action(type=\"omprog\" name=\"support_switch_custom_rule\" binary=\""+os.path.abspath(os.path.join(path,os.pardir))+"/ale_scripts/support_switch_custom_rule.py \\\"Collect log and send notification\\\" \\\"" + get_rule_name(rulename) + "\\\"\")"
                                file.write(rsys_entry+"\n")

                            file.write("stop\n")
                            file.write("}\n")
                            cnt=cnt+1
                        elif cnt<5:
                            cnt=cnt+1
                            continue
                        else:
                            flg=99
                    else:
                        file.write(line)
                file.close()
            os.system("systemctl restart rsyslog") 
            alelog.log_warning_module(request,"Rule updated in db and rsyslog",logger)       
            return Response(message)
            return Response(message)
            
    message = {"Status": "Failure","Message": "User not logged in. Need to login to view this page", "Code": "400"}
    alelog.log_warning_module(request,"No user logged in",logger)
    return Response(message, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PATCH'])
def RuleEnable(request):
    if request.user.is_authenticated==True:
        user = Users.objects.get(user_name = request.user)
        if user.type_id.type_name == 'regular':
            alelog.log_warning_module(request,"Insufficient Permission",logger)
            return Response({"Status": "Failure","Message": "Insufficient Permission","Code": "401"}, status=status.HTTP_401_UNAUTHORIZED)
        ruleid_list=request.data.get('rule_id','')
        print(request.data)
        print(ruleid_list)
        enabled=request.data.get('enabled','')
        invalid_ids=[]
        valid_ids=[]
        for ruleid in ruleid_list:
            try:
                rule=Rules.objects.get(rules_id=ruleid)
                rule.enabled=enabled
                rule.save()
                valid_ids.append(ruleid)
            except Rules.DoesNotExist:
                invalid_ids.append(str(ruleid)+" Not a valid Rule id")
        rules_list={'rule_id':valid_ids,'enabled':enabled}
        message={"Status":"Success","Message":"Sucess","Code":"200","togggle":rules_list} 
        if invalid_ids!=[]:
            message.update({'Invalid rule_id':invalid_ids})
        alelog.log_module(request,"Rules Enabled/Disabled",logger)
        return Response(message)
    message = {"Status": "Failure","Message": "User not logged in. Need to login to view this page", "Code": "400"}
    alelog.log_warning_module(request,"No user logged in",logger)
    return Response(message, status=status.HTTP_400_BAD_REQUEST)

#views for statistics
@api_view(['GET'])
def StatisticsList(request):
    if request.user.is_authenticated==True:
        statistics_list=Statistics.objects.all()
        message={"Status":"Success","Message":"Success","Code":"200"}
        ser=StatisticsSerializer(statistics_list,many=True)
        if ser.data==[]:
            message.update({"Message":"No List exist"})
            alelog.log_module(request,"No Statistics exist",logger)
            return Response(message)
        message.update({'statistics':ser.data})
        alelog.log_module(request,"Statistics list viewed",logger)
        return Response(message)
    message = {"Status": "Failure","Message": "User not logged in. Need to login to view this page", "Code": "400"}
    alelog.log_warning_module(request,"No user logged in",logger)
    return Response(message, status=status.HTTP_400_BAD_REQUEST) 

@api_view(['POST'])
def StatisticsFilter(request):
    if request.user.is_authenticated==True:
        from_date=request.data.get('from_date','')
        to_date=request.data.get('to_date','')
        print(type(to_date))
        message={"Status":"Success","Message":"Success","Code":"200"}
        if to_date>str(date.today()):
            alelog.log_error_module(request,"To date is greater than present date",logger)
            return Response("To date is greater than present date")
        elif from_date>str(date.today()):
            alelog.log_error_module(request,"From date is greater than present date",logger)
            return Response("From date is greater than present date")
        elif to_date<from_date:
            alelog.log_error_module(request,"To date must be greater than from date",logger)
            return Response("To date must be greater than from date")
        statistics_list=Statistics.objects.filter(timestamp__gte=from_date, timestamp__lte=to_date)
        #ser=StatisticsFilterSerializer(statistics_list,many=True)
        ser=StatisticsSerializer(statistics_list,many=True)
        if ser.data==[]:
            message.update({"Message":"No List exist between inputed dates"})
            alelog.log_module(request,"No list exist between inputed dates",logger)
            return Response(message)
        message.update({'statistics':ser.data})
        alelog.log_module(request,"Statistics list viewed",logger)
        return Response(message)
    message = {"Status": "Failure","Message": "User not logged in. Need to login to view this page", "Code": "400"}
    alelog.log_warning_module(request,"No user logged in",logger)
    return Response(message, status=status.HTTP_400_BAD_REQUEST)

#############################
## Test Company Connection ##
#############################

@api_view(['POST'])
def TestConnection(request):
    """
		This function is used for the checking whether the connection is established between Company and Rainbow or not.
	"""

    if request.user.is_anonymous == True:
        message = {
            "Status": "Failure",
            "Message": "User not logged in", 
            "Code": "400"
        }
        alelog.log_warning_module(request,"No user logged in",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

    from mysql.connector import connect
    from cryptography.fernet import Fernet
    db_key=b'gP6lwSDvUdI04A8fC4Ib8PXEb-M9aTUbeZTBM6XAhpI='
    dbsecret_password=b'gAAAAABivYWTJ-2OZQW4Ed2SGRNGayWRUIQZxLckzahNUoYSJBxsg5YZSYlMdiegdF1RCAvG4FqjMXD-nNeX0i6eD7bdFV8BEw=='
    fernet = Fernet(db_key)
    db_password = fernet.decrypt(dbsecret_password).decode()
    database = connect(
            host='localhost',
            user='aletest',
            password=db_password,
            database='aledb'
            )
    db = database.cursor()
    query = "SELECT * FROM `ALEUser_settings_value`"
    db.execute(query)
    result = json.loads(db.fetchall()[1][2])

    room_id = result["room_id"]
    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    database.close()
    company_name = request.data['company_name']
    url = "https://vna.preprod.omniaccess-stellar-asset-tracking.com//api/flows/NBDNotif_Test_{0}/".format(company_name)
    headers = {
        'Content-type': 'application/json',
        "Accept-Charset": "UTF-8",
        'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
        'subject': '{0}'.format('Testing Connection'),
        'action': '{0}'.format('Testing the connection for Rainbow'),
        'result': '{0}'.format('Status: Pending'),
        'roomid': room_id,
        'Card': '0',
        'Email': '0',
        'Advanced': '0'
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        message = {
            "Status": "Success",
            "Message": "Connection Established",
            "Code": "200",
            "Rainbow response": response.text
        }
        alelog.log_module(request,"Test Connection Established",logger)
        return Response(message, status = status.HTTP_200_OK)

    else:
        message = {
            "Status": "Failure",
            "Message": "Connection was not able to establish",
            "Code": response.status_code,
            "Rainbow response": response.text
        }
        alelog.log_error_module(request,"Test connection Failed",logger)
        return Response(message, status = status.HTTP_404_NOT_FOUND)

##################
## Settings Tab ##
##################
@csrf_exempt
def SettingsPost(request):
	#	This function is used for the fetching the details of setting tab.
    if request.user.is_anonymous == True:
        message = {
			"Status": "Failure",
			"Message": "User not logged in", 
			"Code": "400"
        }
        alelog.log_warning_module(request,"No user logged in",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)
    
    user = Users.objects.get(user_name = request.user)
    if user.type_id.type_name == 'regular':
        message = {
			"Status": "Failure",
			"Message": "Insufficient Permission",
			"Code": "401"
        }
        alelog.log_warning_module(request,"No user logged in",logger)
        return Response(message, status=status.HTTP_401_UNAUTHORIZED)
    try:
        path=os.path.dirname(__file__)
        prev_ports = []
        new_ports = []
        json_data = {
			"name": request.data.get("company_name", ''),
			"value": {
				"ssh_port": request.data.get("ssh_port", ''),
				"rsyslog_port": request.data.get("rsyslog_port", ''),
				"grafana_port": request.data.get("grafana_port", '')
    		}
    	}
        
        settings_data = Settings_Value.objects.all()
        
        if len(settings_data) == 0:
            settings = SettingsSerializer(data=json_data)
        else:
            settings_data = settings_data[0]
            settings = SettingsSerializer(instance=settings_data, data=json_data)
            prev_settings = SettingsSerializer(settings_data)
            
            
            for key, value in prev_settings.data['value'].items():
                prev_ports.append((key, value))
                
        firewall_status = ufw.status()
        print('firewall status', firewall_status)
        
        if settings.is_valid():	    	
            settings = settings.save()
            
            for key, value in settings.value.items():
                new_ports.append((key, value))
                
            message = {
    			"Status": "Success",
				"Message": "Setting Details",
				"Code": "200",
				"settings_data": {
					"ssh_port": settings.value["ssh_port"],
					"rsyslog_port": settings.value["rsyslog_port"],
					"grafana_port": settings.value["grafana_port"],
					"company_name": settings.name
				}
    		}
            
            for port_name, port_val in prev_ports:
                string = "allow {0}".format(port_val)
                if port_name.lower() == "ssh_port":
                    string += "/tcp"
                elif port_name.lower() == "rsyslog_port":
                    string += "/udp"

                ufw.delete(string)
                print('Deleted Port: ', port_val)
                
            for port_name, port_val in new_ports:
                string = "allow {0}".format(port_val)
                if port_name.lower() == "ssh_port":
                    string += "/tcp"
                elif port_name.lower() == "rsyslog_port":
                    string += "/udp"

                ufw.add(string)
                print('Added Port: ', port_val)

            old_ssh_port = prev_settings.data['value']['ssh_port']
            new_ssh_port = settings.value["ssh_port"]
            old_rsyslog_port = prev_settings.data['value']['rsyslog_port']
            new_rsyslog_port = settings.value["rsyslog_port"]

            subprocess.call(["sed -i 's/-A INPUT -p tcp -m tcp --dport {0} -j ACCEPT/-A INPUT -p tcp -m tcp --dport {1} -j ACCEPT/g' /etc/iptables/rules.v4".format(old_ssh_port, new_ssh_port)], shell=True)
            subprocess.call(["sed -i 's/-A ufw-user-input -p tcp -m tcp --dport {0} -j ACCEPT/-A ufw-user-input -p tcp -m tcp --dport {1} -j ACCEPT/g' /etc/iptables/rules.v4".format(old_ssh_port, new_ssh_port)], shell=True)
            subprocess.call(["sed -i 's/-A INPUT -p udp -m udp --dport {0} -j ACCEPT/-A INPUT -p udp -m udp --dport {1} -j ACCEPT/g' /etc/iptables/rules.v4".format(old_rsyslog_port, new_rsyslog_port)], shell=True)
            subprocess.call(["sed -i 's/-A ufw-user-input -p udp -m udp --dport {0} -j ACCEPT/-A ufw-user-input -p udp -m udp --dport {1} -j ACCEPT/g' /etc/iptables/rules.v4".format(old_rsyslog_port, new_rsyslog_port)], shell=True)

            subprocess.call(["sed -i 's/-A INPUT -p tcp -m tcp --dport {0} -j ACCEPT/-A INPUT -p tcp -m tcp --dport {1} -j ACCEPT/g' /etc/iptables/rules.v6".format(old_ssh_port, new_ssh_port)], shell=True)
            subprocess.call(["sed -i 's/-A ufw6-user-input -p tcp -m tcp --dport {0} -j ACCEPT/-A ufw6-user-input -p tcp -m tcp --dport {1} -j ACCEPT/g' /etc/iptables/rules.v6".format(old_ssh_port, new_ssh_port)], shell=True)
            subprocess.call(["sed -i 's/-A INPUT -p udp -m udp --dport {0} -j ACCEPT/-A INPUT -p udp -m udp --dport {1} -j ACCEPT/g' /etc/iptables/rules.v6".format(old_rsyslog_port, new_rsyslog_port)], shell=True)
            subprocess.call(["sed -i 's/-A ufw6-user-input -p udp -m udp --dport {0} -j ACCEPT/-A ufw6-user-input -p udp -m udp --dport {1} -j ACCEPT/g' /etc/iptables/rules.v6".format(old_rsyslog_port, new_rsyslog_port)], shell=True)

            os.system('/sbin/iptables-save | tee /etc/iptables/rules.v4')
            os.system('/sbin/ip6tables-save | tee /etc/iptables/rules.v6')
            os.system('/sbin/iptables-save')
            os.system('/sbin/ip6tables-save')

            subprocess.call(["sed -i 's/Port {0}/Port {1}/g' /etc/ssh/sshd_config".format(old_ssh_port, new_ssh_port)], shell=True)
            subprocess.call(["sed -i 's/input(type=\"imudp\" port=\"{0}\")/input(type=\"imudp\" port=\"{1}\")/g' /etc/rsyslog.conf".format(old_rsyslog_port, new_rsyslog_port)], shell=True)

            enable_syslog_path = os.path.abspath(os.path.join(path,os.pardir))+"/ale_scripts/enable_syslogs.py \\\"{0}\\\"".format(new_rsyslog_port)
            os.system("python3 {0}".format(enable_syslog_path))

            os.system("systemctl restart ssh")
            os.system("systemctl restart rsyslog")

            alelog.log_module(request,"Setting Details",logger)
            return Response(message, status=status.HTTP_200_OK)
            
        message = {
			"Status": "Failure",
			"Message": "Settings Table Data Updation Failure",
			"Code": "400",
			"Error Message": "Unable to Update the Details in Settings Table"
    	}
        alelog.log_error_module(request,"Settings Table Data Updation Failed",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as exception:
        message = {
			"Status": "Failure",
			"Message": "Updating Settings Table Data Failed",
			"Code": "400",
			"Error Message": exception.args
    	}
        alelog.log_error_module(request,"Updating Settings Table Data Failed",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

def SettingsFetch(request):
    """
        This function is used for the fetching the details of setting tab.
    """

    if request.user.is_anonymous == True:
        message = {
            "Status": "Failure",
            "Message": "User not logged in", 
            "Code": "400"
        }
        alelog.log_warning_module(request,"No user logged in",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

    user = Users.objects.get(user_name = request.user)
    if user.type_id.type_name == 'regular':
        message = {
            "Status": "Failure",
            "Message": "Insufficient Permission",
            "Code": "401"
        }
        alelog.log_warning_module(request,"Insufficient Permission",logger)
        return Response(message, status=status.HTTP_401_UNAUTHORIZED)
    try:
        settings_data = Settings_Value.objects.all()
        if len(settings_data):
            settings_data = settings_data[0]
            settings = SettingsSerializer(settings_data)
            message = {
                "Status": "Success",
                "Message": "Setting Details",
                "Code": "200",
                "settings_data": {
                    "ssh_port": settings.data['value']["ssh_port"],
                    "rsyslog_port": settings.data['value']["rsyslog_port"],
                    "grafana_port": settings.data['value']["grafana_port"],
                    "company_name": settings.data['name']
                }
            }
        else:
            message = {
    			"Status": "Success",
    			"Message": "No Setting Details Present",
    			"Code": "200",
    			"Error Message": "No Data Present"
    		}
        alelog.log_error_module(request,"No Settings Details present",logger)
        return Response(message, status=status.HTTP_200_OK)
    
    except Exception as exception:
        message = {
    		"Status": "Failure",
    		"Message": "Fetching Settings Table Data Failed",
    		"Code": "400",
    		"Error Message": exception.args
    	}
        alelog.log_error_module(request,"Fetching Settings Table Data Failed",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
def SettingsFunctionDistributor(request):
    if request.method == 'GET':
        return SettingsFetch(request)

    elif request.method == 'POST':
       return SettingsPost(request)

@api_view(['GET'])
def aboutApi(request):
    if request.user.is_authenticated==True:
        hdd_details = psutil.disk_usage("/")
        hostname=socket.gethostname()
        ramusage=psutil.virtual_memory()
        company_name = Settings_Value.objects.get(id=1).name
        os_details = {}
        for i in os.popen('cat /etc/os-release').read().split("\n"):
            i=str(i).split('=')
            if len(i)>1:
                os_details[i[0]]=i[1].replace("\"","")
        url = "https://tpe-vna.al-mydemo.com/api/flows/NBDNotif_Test_"+company_name
        headers = {
            'Content-type': 'application/json',
            "Accept-Charset": "UTF-8",
            'X-VNA-Authorization': "7ad68b7b-00b5-4826-9590-7172eec0d469",
            'subject': '{0}'.format('Testing Connection'),
            'action': '{0}'.format('Testing the connection for Rainbow'),
            'result': '{0}'.format('Status: Pending'),
            'Card': '0',
            'Email': '0',
            'Advanced': '0'
        }
        print(url)
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                status="Success"
            else:
                status="Fail"
        except ConnectionError as e:
            status="Fail"
        
        output = subprocess.check_output("sudo apt-get update", shell=True)
        build_available_version_binary = subprocess.check_output("sudo apt list | grep preventivemaintenance", shell=True)
        build_available_version_binary = build_available_version_binary.split()[1]
        build_available_version = str(build_available_version_binary, 'utf-8')

        current_version_binary = subprocess.check_output("sudo apt list --installed | grep preventivemaintenance", shell=True)
        current_version_binary = current_version_binary.split()[1]
        current_version = str(current_version_binary, 'utf-8')

        message = { 
            "status": "success",
            "message": "success",
            "code": "200",
            "version": {
                "current_release": "2.0",
                "ale_repository_build_available": build_available_version,
                "build": current_version,
                "vna_rainbow_status": status
            },
            "system": {
                "hostname": hostname,
                #"ip_address": socket.gethostbyname(hostname),
                #"mac_address": hex(uuid.getnode()),
                #"operating_system": platform.system(),
                #"version_distribution": platform.version(),
                #"architecture": " ".join(platform.architecture()),
                "ip_address": socket.gethostbyname(str(hostname)+'.local'),
                "mac_address": os.popen('cat /sys/class/net/*/address').read().split("\n")[0],
                "operating_system": os_details['NAME'],
                "version_distribution": os_details['VERSION'],
                "architecture": os_details['ID'],
                "total_memory": math.ceil(ramusage[0]/(2**30)),
                "free_memory": math.ceil(ramusage[4]/(2**30)),
                "cpu": os.cpu_count()
                #os.cpu_count()
            },
            "hard_disk": {
                "total_memory": int(hdd_details.total / (2**30)),
                "free_memory": int(hdd_details.free/ (2**30))
            }
	    }
        alelog.log_module(request,"About system config and rainbow status viewed",logger)
        return Response(message)
    message = {"Status": "Failure","Message": "User not logged in. Need to login to view this page", "Code": "400"}
    alelog.log_warning_module(request,"No user logged in",logger)
    return Response(message)#, status=status.HTTP_400_BAD_REQUEST)

# Download django apis logs

@api_view(['GET'])
def log_Download(request):
    if request.user.is_authenticated==True:
        try:
            alelog.log_module(request,"Logs filed downloaded",logger)
            return FileResponse(open('./timelog.log', 'rb'))
        except:
            message = {"Status": "Failure","Message": "Log Download Failed", "Code": "400"}
            alelog.log_error_module(request,"Logs download failed",logger)
            return Response(message)
    message = {"Status": "Failure","Message": "User not logged in. Need to login to view this page", "Code": "400"}
    alelog.log_warning_module(request,"No user logged in",logger)
    return Response(message)

#################################
## Upload Script Offline API's ##
#################################

template = '''
template (name="{0}" type="string" 
    string="/var/log/devices/{1}.json")
'''

rule = '''
{0} then {{
    $RepeatedMsgReduction on
    action(type="omfile" DynaFile="deviceloghistory" template="json_syslog" DirCreateMode="0755" FileCreateMode="0755")
    action(type="omfile" DynaFile="{4}" template="json_syslog" DirCreateMode="0755" FileCreateMode="0755")
    action(type="omprog" name="{1}" binary="{2} \\\"{3}\\\"" queue.type="LinkedList" queue.size="1" queue.workerThreads="1")
    stop
}}
:syslogtag, contains, "montag" /var/log/devices/script_execution.log
& stop
'''

@api_view(['POST'])
def ImportScripts(request):
    if request.user.is_anonymous == True:
        message = {
            "Status": "Failure",
            "Message": "User not logged in", 
            "Code": "400"
        }
        alelog.log_warning_module(request,"No user logged in",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

    user = Users.objects.get(user_name = request.user)
    if user.type_id.type_name == 'regular':
        message = {
            "Status": "Failure",
            "Message": "Insufficient Permission",
            "Code": "401"
        }
        alelog.log_warning_module(request,"Insufficient Permissons to upload file",logger)
        return Response(message, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        # source and destination paths
        source_path = str(os.path.join(Path.home(), "Downloads", "extract"))
        destination_path = str(os.path.join(os.getcwd(), "ale_scripts"))

        # extracting the zip file and saving the Downloads Folder
        _zipfile= zipfile.ZipFile(request.FILES['script'])
        _zipfile.extractall(source_path)

        # path to source folder after extraction
        script_folder = [ name for name in os.listdir(source_path) if os.path.isdir(os.path.join(source_path, name)) ][0]
        script_folder_path = str(os.path.join(source_path, script_folder))

        # fetching of the excel file
        csv_files = glob.glob(os.path.join(source_path, "*.xlsx"))
        print('csv files', csv_files)

        f = csv_files[0]

        # read the csv file
        df = pd.read_excel(f)                                        
        head = df.head()
        print('head:', head)

        for index, row in df.iterrows():
            print('data -> ', index, row['Pattern'], row['Script'])
            pattern = row['Pattern']
            script = row['Script']
            dynaFile = row['DynaFile']
            log_filename = row['LogFilename']
            commandlineArgs = row['CommandLineArgs']
            description = row['Description']

            if len(script.split(' ')) > 1:
                python_script, data = script.split(' ', 1)
                data = "\\\"{0}\\\"".format(data)
            else:
                python_script, data = script, ''

            # python script destination path
            source = str(os.path.join(script_folder_path, python_script))
            destination = str(os.path.join(destination_path, python_script))

            # move the file from source to destination
            shutil.move(source, destination)

            # create/update rule
            action = 'Execute Scripts'  
            action = Actions.objects.get(action = action)
            ruletype = RulesTypes.objects.get(type_name = 'Default')

            rules, rules_created_bool = Rules.objects.update_or_create(rule_name = pattern,
                                                                        defaults = {
                                                                            'rule_type_id': ruletype,
                                                                            'action_id': action,
                                                                            'enabled': True,
                                                                            'timeout': 5,
                                                                            'rule_description': description
                                                                        })
            
            # _rule = Rules.objects.filter(rule_name = pattern)
            # if len(_rule) == 0:
            #     rules = Rules.objects.create(rule_name = pattern, 
            #                                 rule_type_id = ruletype, 
            #                                 action_id = action, 
            #                                 enabled = True, 
            #                                 timeout = 5, 
            #                                 rule_description = description)

            # rsyslog template
            rsyslog_template_flag = True
            rsyslog_template = template.format(dynaFile, log_filename)

            # if rule is already present in rsyslog.conf then remove it
            with open(r'/etc/rsyslog.conf', "r") as file_input:
                file_data = file_input.readlines()

            with open(r'/etc/rsyslog.conf', "w") as output: 
                count = 0
                while file_data:
                    line = file_data.pop(0)

                    if rsyslog_template_flag and 'template (name=\"{0}\" type=\"string\"'.format(dynaFile) in line.strip("\n"):
                        rsyslog_template_flag = False
                        file_data.pop(0)
                        output.write(rsyslog_template.lstrip("\n")) 
                        continue

                    if pattern in line.strip("\n"):
                        if '{' in line:
                            count += 1
                            
                        while count:
                            line = file_data.pop(0)
                            if '{' in line:
                                count += 1
                            elif '}' in line:
                                count -= 1
                        
                        file_data.pop(0)

                    elif count == 0:
                        output.write(line)

            # write in Rsyslog.conf
            rsyslog_rule = rule.format(pattern, python_script.split('.')[0], destination + ((' ' + data) if data else ''), commandlineArgs, dynaFile)

            with open(r'/etc/rsyslog.conf', 'r+') as fp:
                # read an store all lines into list
                lines = fp.readlines()
                # move file pointer to the beginning of a file
                fp.seek(0)
                # truncate the file
                fp.truncate()

                # start writing lines except the last line
                # lines[:-1] from line 0 to the second last line
                fp.writelines(lines[:-2])

            with open(r'/etc/rsyslog.conf', 'a+') as file:
                if rsyslog_template_flag:
                    file.write(rsyslog_template)

                file.write(rsyslog_rule)

            # changing the permissions of the files
            os.chmod(destination, 0o755)
            shutil.chown(destination, 'admin-support', 'admin-support')

        # delete the folder
        # shutil.rmtree(source_path)

        # restart the rsyslog
        os.system("systemctl restart rsyslog")

        message = {
            "Status": "Success",
            "Message": "Data Creation/Modification Success",
            "Code": "200"
        }
        alelog.log_module(request,"Uploaded and imported rules",logger)
        return Response(message, status=status.HTTP_200_OK)
    
    except Exception as e:
        # delete the folder
        # shutil.rmtree(source_path, ignore_errors = True)

        # restart the rsyslog
        os.system("systemctl restart rsyslog")

        message = {
            "Status": "Failure",
            "Message": "(e)",
            "Code": "400"
        }
        alelog.log_module(request,"Failed to Uploaded and imported rules, ERROR" + str(e),logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)


# profile edit/view 
@api_view(['GET','PUT'])
def UserProfile(request):
    if request.method=='GET':
        if request.user.is_authenticated==True:
            print(request.user.id)
            login_user = Users.objects.get(user_name=request.user)
            message={"Status":"Success","Message":"User data","Code":"200","user":
            {"name":login_user.user_name.username,"email_id":login_user.email,"rainbow_jid":login_user.jid}}
            alelog.log_module(request,"User profile viewed",logger)
            return Response(message)
        alelog.log_warning_module(request,"No user logged in",logger)
        message = {"Status": "Failure","Message": "User not logged in. Need to login to view this page", "Code": "400"}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)
    elif request.method=='PUT':
        if request.user.is_authenticated==True:
            print(request.user.id)
            update_username=request.data.get('name','')
            update_email_id=request.data.get('email_id','')
            update_rainbow_jid=request.data.get('rainbow_jid','')
            login_user = Users.objects.get(user_name=request.user)
            print(login_user.user_name)
            if update_username!=login_user.user_name.username:
                if User.objects.filter(username=update_username).exists():
                    message = {"Status": "Failure","Message": "User name already exist", "Code": "400"}
                    alelog.log_error_module(request,"Update username -User name already exist",logger)
                    return Response(message, status=status.HTTP_400_BAD_REQUEST)
            if update_email_id!=login_user.email:
                if Users.objects.filter(email=update_email_id).exists():
                    message = {"Status": "Failure","Message": "Email Id already exist", "Code": "400"}
                    alelog.log_error_module(request,"Update Email- Email Id already exist",logger)
                    return Response(message, status=status.HTTP_400_BAD_REQUEST)
            if update_rainbow_jid!=login_user.jid:
                if Users.objects.filter(jid=update_rainbow_jid).exists():
                    message = {"Status": "Failure","Message": "Rainbow  JId already exist", "Code": "400"}
                    alelog.log_error_module(request," Update Rainbow Jid - Rainbow Jid Already exist",logger)
                    return Response(message, status=status.HTTP_400_BAD_REQUEST)
            user=User.objects.get(username=request.user)
            user.username=update_username
            user.email=update_email_id
            user.save()
            login_user.email=update_email_id
            login_user.jid=update_rainbow_jid
            login_user.save()        
            message={"Status":"Success","Message":"User profile updated","Code":"200","user":
            {"name":update_username,"email_id":update_email_id,"rainbow_jid":update_rainbow_jid}}
            alelog.log_error_module(request,"Profile updated successfully",logger)
            return Response(message)
        message = {"Status": "Failure","Message": "User not logged in. Need to login to view this page", "Code": "400"}
        alelog.log_warning_module(request,"No user logged in",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)


#################################
## Upgrade from ALE Repository ##
#################################

template = '''
template (name="{0}" type="string" 
    string="/var/log/devices/{1}.json")
'''

rule = '''
{0} then {{
    $RepeatedMsgReduction on
    action(type="omfile" DynaFile="deviceloghistory" template="json_syslog" DirCreateMode="0755" FileCreateMode="0755")
    action(type="omfile" DynaFile="{4}" template="json_syslog" DirCreateMode="0755" FileCreateMode="0755")
    action(type="omprog" name="{1}" binary="{2} \\\"{3}\\\"" queue.type="LinkedList" queue.size="1" queue.workerThreads="1")
    stop
}}
:syslogtag, contains, "montag" /var/log/devices/script_execution.log
& stop
'''

@api_view(['GET'])
def UpgradeFromALE(request):
    if request.user.is_anonymous == True:
        message = {
            "Status": "Failure",
            "Message": "User not logged in", 
            "Code": "400"
        }
        alelog.log_warning_module(request,"No user logged in",logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

    user = Users.objects.get(user_name = request.user)
    if user.type_id.type_name == 'regular':
        message = {
            "Status": "Failure",
            "Message": "Insufficient Permission",
            "Code": "401"
        }
        alelog.log_warning_module(request,"Insufficient Permissons to upload file",logger)
        return Response(message, status=status.HTTP_401_UNAUTHORIZED)

    os.system("sudo apt-get update")
    # os.system("apt list | grep preventivemaintenance")
    os.system("sudo apt-get --only-upgrade install preventivemaintenance")

    try:
        # source path and destination paths
        source_path = r'/opt/ALE_Scripts'
        destination_path = str(os.path.join(os.getcwd(), "ale_scripts"))

        # path to source folder after extraction
        script_folder = [ name for name in os.listdir(source_path) if os.path.isdir(os.path.join(source_path, name)) ][0]
        script_folder_path = str(os.path.join(source_path, script_folder))

        # fetching of the excel file
        csv_files = glob.glob(os.path.join(source_path, "*.xlsx"))
        print('csv files', csv_files)

        f = csv_files[0]

        # read the csv file
        df = pd.read_excel(f)                                        
        head = df.head()
        print('head:', head)

        for index, row in df.iterrows():
            print('data -> ', index, row['Pattern'], row['Script'])
            pattern = row['Pattern']
            script = row['Script']
            dynaFile = row['DynaFile']
            log_filename = row['LogFilename']
            commandlineArgs = row['CommandLineArgs']
            description = row['Description']

            if len(script.split(' ')) > 1:
                python_script, data = script.split(' ', 1)
                data = "\\\"{0}\\\"".format(data)
            else:
                python_script, data = script, ''

            # python script destination path
            source = str(os.path.join(script_folder_path, python_script))
            destination = str(os.path.join(destination_path, python_script))

            # copy the file from source to destination
            shutil.copyfile(source, destination)

            # create/update rule
            action = 'Execute Scripts'  
            action = Actions.objects.get(action = action)
            ruletype = RulesTypes.objects.get(type_name = 'Default')

            rules, rules_created_bool = Rules.objects.update_or_create(rule_name = pattern,
                                                                        defaults = {
                                                                            'rule_type_id': ruletype,
                                                                            'action_id': action,
                                                                            'enabled': True,
                                                                            'timeout': 5,
                                                                            'rule_description': description
                                                                        })
            
            # _rule = Rules.objects.filter(rule_name = pattern)
            # if len(_rule) == 0:
            #     rules = Rules.objects.create(rule_name = pattern, rule_type_id = ruletype, action_id = action, enabled = True, timeout = 5, rule_description = description)

            # rsyslog template
            rsyslog_template_flag = True
            rsyslog_template = template.format(dynaFile, log_filename)

            # if rule is already present in rsyslog.conf then remove it
            with open(r'/etc/rsyslog.conf', "r") as file_input:
                file_data = file_input.readlines()

            with open(r'/etc/rsyslog.conf', "w") as output: 
                count = 0
                while file_data:
                    line = file_data.pop(0)

                    if rsyslog_template_flag and 'template (name=\"{0}\" type=\"string\"'.format(dynaFile) in line.strip("\n"):
                        rsyslog_template_flag = False
                        file_data.pop(0)
                        output.write(rsyslog_template.lstrip("\n")) 
                        continue

                    if pattern in line.strip("\n"):
                        if '{' in line:
                            count += 1
                            
                        while count:
                            line = file_data.pop(0)
                            if '{' in line:
                                count += 1
                            elif '}' in line:
                                count -= 1
                        
                        file_data.pop(0)

                    elif count == 0:
                        output.write(line)

            # write in Rsyslog.conf
            rsyslog_rule = rule.format(pattern, python_script.split('.')[0], destination + ((' ' + data) if data else ''), commandlineArgs, dynaFile)

            with open(r'/etc/rsyslog.conf', 'r+') as fp:
                # read an store all lines into list
                lines = fp.readlines()
                # move file pointer to the beginning of a file
                fp.seek(0)
                # truncate the file
                fp.truncate()

                # start writing lines except the last line
                # lines[:-1] from line 0 to the second last line
                fp.writelines(lines[:-2])

            with open(r'/etc/rsyslog.conf', 'a+') as file:
                if rsyslog_template_flag:
                    file.write(rsyslog_template)

                file.write(rsyslog_rule)

            # changing the permissions of the files
            os.chmod(destination, 0o755)
            shutil.chown(destination, 'admin-support', 'admin-support')

        # delete the folder
        # shutil.rmtree(source_path)

        # restart the rsyslog
        os.system("systemctl restart rsyslog")

        message = {
            "Status": "Success",
            "Message": "Data Creation/Modification Success",
            "Code": "200"
        }
        alelog.log_module(request,"Uploaded and imported rules from ALE Repo",logger)
        return Response(message, status=status.HTTP_200_OK)

    except:
        # delete the folder
        # shutil.rmtree(source_path, ignore_errors = True)

        # restart the rsyslog
        os.system("systemctl restart rsyslog")

        message = {
            "Status": "Failure",
            "Message": "Data Creation/Modification Failure",
            "Code": "400"
        }
        alelog.log_module(request,"Failed to Uploaded and imported rules from ALE Repo, ERROR" + str(e),logger)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

