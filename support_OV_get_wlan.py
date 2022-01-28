#!/usr/bin/python
import requests, json
import os
import datetime
import re
from time import gmtime, strftime, localtime, sleep, time

User="jtrebaol"
Pass="OmniVista2500*"
IP="labjtr.ov.ovcirrus.com"
device_mac="34:42:62:ed:58:74"
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

class OvHandler:

    def __init__(self):
        url = "https://"+ IP + ":443/api/"
        self.ov = url
        self.cookies = dict()
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
                           headers={ 'Ov-App-Version' : '4.4R2', 'content-type': 'application/json' })
        try:
            info = "The post server response : \n {0} \n ".format(r.text)
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

    def postWLANClient(self,device_mac):
        channel = clientName = None
        data = {'filterConditions':[{'attribute':'clientMac','value': [device_mac]}],'orderBy': 'clientName','orderType':'ASC','pageNumber': 1,'pageSize': 1000}
        r=self.post('wma/onlineClient/getOnlineClientListByPage',data)
        python_obj = json.loads( json.dumps(r, sort_keys=True, indent=4, separators=(',', ': ')))
        data_1 = python_obj["data"]
        data_2 = data_1["data"]
        for element in data_2:
          if "channel" in element:
             element = json.dumps(element)
             channel = re.findall(r"\"channel\": \"(.*?)\"", element)[0]
             print(channel)
        for element in data_2:
          if "clientName" in element:
             element = json.dumps(element)
             clientName = re.findall(r"\"clientName\": \"(.*?)\"", element)[0]
             print(clientName)
        return channel,clientName

    def postWLANIoT(self,device_mac):
        category = None
        data = {
                 "type":"IotInventoryRequest",
                 "endpointStatus":"All",
                 "filterBy":"DEVICE",
                 "macAddresses":[device_mac],
                 "categories":[],
                 "unps":[],
                 "ssids":[],
                 "deviceMap":{},
                 "apGroups":None,
                 "mapIds":None,
                 "timeRange":None,
                 "pageSize":1000,
                 "pageNumber":1,
                 "debugMode":"false",
                 "latestRecords":"true"
                }
        r=self.post('iot/inventory',data)

        python_obj = json.loads( json.dumps(r, sort_keys=True, indent=4, separators=(',', ': ')))
        data_1 = python_obj["response"]["ioTInventoryVOs"]
        for element in data_1:
          if "category" in element:
             element = json.dumps(element)
             print("\n")
             category = re.findall(r"\"type\": \"(.*?)\"", element)[0]
             print(category)
        return category

#def main():
    # Create OV REST Session
#    ovrest = OvHandler()
#    info = "----Test Python Script"
#    entry_log(info)
#    ovrest.postWLANClient(device_mac)
#    ovrest.postWLANIoT(device_mac)

#main()
