#!/usr/bin/env python3
import requests
import json
import os
import datetime
import sys

# ------------------------------------------------------------------------------

IP = sys.argv[1]
User = sys.argv[2]
Pass = sys.argv[3]


class OvHandler:

    def __init__(self):
        url = "https://" + IP + ":443/api/"
        self.ov = url
        self.cookies = dict()
       # print(self.cookies)

    def post(self, path, obj):
        fullpath = self.ov + path
        print("In post path %s" % fullpath)

        r = requests.post(fullpath, json.dumps(obj),
                          cookies=self.cookies,
                          verify=False,
                          headers={'content-type': 'application/json'})
        try:
            print(r.text)
            return json.loads(r.text)
        except ValueError:
            return {}

    def get(self, path):
        r = requests.get(self.ov + path,
                         cookies=self.cookies,
                         verify=False,
                         headers={'content-type': 'application/json'})

        try:
            #print (r.text)
            return json.loads(r.text)
        except ValueError:
            print("Exception")
            return {}

    def getOVInfo(self):
        if not 'accessToken' in self.cookies:
            login = self.post('login', {'userName': User, 'password': Pass})
            self.cookies['accessToken'] = login['accessToken']

        r = self.get('about')
        print(json.dumps(r, sort_keys=True, indent=4, separators=(',', ': ')))

    def getOVTopologySites(self):
        r = self.get('topology/sites')
        print(json.dumps(r, sort_keys=True, indent=4, separators=(',', ': ')))

    def getDeviceDetails(self):
        r = self.get('devices')
        print(json.dumps(r, sort_keys=True, indent=4, separators=(',', ': ')))

    def getPorts(self):
        r = self.get('port?deviceIds="5fda200fe4b0b035a5ce85ad"')
        print(json.dumps(r, sort_keys=True, indent=4, separators=(',', ': ')))

    def getWLANService(self):
        r = self.post('ag/wlan-service')
        print(json.dumps(r, sort_keys=True, indent=4, separators=(',', ': ')))


def main():
    # Create OV REST Session
    ovrest = OvHandler()
    print("----Test Python Script")
    ovrest.getOVInfo()
#    ovrest.getOVTopologySites()
#    ovrest.getDeviceDetails()
    ovrest.getWLANService()


main()
