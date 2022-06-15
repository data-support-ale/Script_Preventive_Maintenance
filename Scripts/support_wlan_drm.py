#!/usr/local/bin/python3.7

import sys
import os
import json
import re
from time import strftime, localtime
from support_tools_OmniSwitch import get_credentials
from support_send_notification import send_message
from database_conf import *

runtime = strftime("%d_%b_%Y_%H_%M_%S", localtime())

switch_user, switch_password, mails, jid, ip_server, login_AP, pass_AP, tech_pass, random_id, company = get_credentials()

last = ""
with open("/var/log/devices/lastlog_drm.json", "r", errors='ignore') as log_file:
    for line in log_file:
        last = line

with open("/var/log/devices/lastlog_drm.json", "w", errors='ignore') as log_file:
    log_file.write(last)

with open("/var/log/devices/lastlog_drm.json", "r", errors='ignore') as log_file:
    try:
        log_json = json.load(log_file)
        ipadd = log_json["relayip"]
        host = log_json["hostname"]
        msg = log_json["message"]
    except json.decoder.JSONDecodeError:
        print("File /var/log/devices/lastlog_drm.json empty")
        exit()
    # Sample log
    # <INFO> [AP 34:E7:0B:xx:xx:00@172.16.102.54] ：2.4G/5G channel utilization 50%/37%, channel 1/149, power 20/22, band width 20M/20M, station number 0/3
    if "channel utilization" in msg:
        try:
            band_24, band_5, channel_utilization_24, channel_utilization_5, channel_24, channel_5, power_24, power_5, width_24, width_5, station_no_24, station_no_5 = re.findall(r"(.*?)/(.*?) channel utilization (.*?)/(.*?), channel (.*?)/(.*?), power (.*?)/(.*?), band width (.*?)/(.*?), station number (.*?)/(.*?).", msg)[0]
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "Band 2.4GHz (channel utilization / number of clients)": channel_utilization_24/station_no_24, "Band 5GHz (channel utilization / number of clients)": channel_utilization_5/station_no_5}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass 
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
    # Sample log
    # <WARNING> [AP 34:E7:0B:xx:xx:00@172.16.102.54] ：2.4G channel utilization exceeded the threshold 90%.
    elif "channel utilization exceeded" in msg:
        try:
            band, channel_utilization = re.findall(r"(.*?) channel utilization exceeded the threshold (.*?).", msg)[0]
            info = "Preventive Maintenance Application - WLAN Stellar AP {} Channel on Radio band {}Hz exceeds the threshold {}. Please increase the Channel Width on your RF Profile. Recommendation is to increase the width for closed location with lot of WLAN clients. Take care of overlap with other channels".format(ipadd, band, channel_utilization)
            send_message(info, jid)
            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP": ipadd, "Band": band, "Channel Utilization": channel_utilization}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass 
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
    # Sample log
    # Notify neighbor AP 172.16.102.66 of my channel, and neighbor AP channel is 1 36 149, my channel is 1 36 0
    elif "Notify neighbor AP" in msg:
        try:
            neighbor_ip, neighbor_channel_24, neighbor_channel_5, neighbor_channel_5_high, my_channel_24, my_channel_5, my_channel_5_high = re.findall(r"Notify neighbor AP (.*?) of my channel, and neighbor AP channel is (.*?) (.*?) (.*?), my channel is (.*?) (.*?) (.*?)", msg)[0]

            try:
                write_api.write(bucket, org, [{"measurement": str(os.path.basename(__file__)), "tags": {
                                "IP / Neighbor IP": ipadd / neighbor_ip, "Band 2.4GHz Channels": my_channel_24 / neighbor_channel_24, "Band 5GHz Channels": my_channel_5 / neighbor_channel_5, "Band 5GHz High Channels": my_channel_5_high / neighbor_channel_5_high}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass 
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
        if my_channel_24==neighbor_channel_24:
            info = "Preventive Maintenance Application - WLAN Stellar AP {} Channel on Radio band 2.4GHz uses the same Channel {} as Neighbor AP {}. Please change the RF Profile Channel Setting/Channel List".format(ipadd,neighbor_channel_24,neighbor_ip)
            send_message(info, jid)
        elif my_channel_5==neighbor_channel_5:
            print(neighbor_ip)
            print(neighbor_channel_5)
            info = "Preventive Maintenance Application - WLAN Stellar AP {} Channel on Radio band 5GHz uses the same Channel {} as Neighbor AP {}. Please change the RF Profile Channel Setting/Channel List".format(ipadd,neighbor_channel_5,neighbor_ip)
            send_message(info, jid)   
        elif my_channel_5_high==neighbor_channel_5_high:
            print(neighbor_ip)
            print(neighbor_channel_5_high)
            info = "Preventive Maintenance Application - WLAN Stellar AP {} Channel on Radio band 5GHz uses the same Channel {} as Neighbor AP {}. Please change the RF Profile Channel Setting/Channel List".format(ipadd,neighbor_channel_5_high,neighbor_ip)
            send_message(info, jid) 
        else:
            print("Channels are differents")
    # Sample log
    # Wireless drm[17849] <NOTICE> [AP DC:08:56:36:17:80@10.130.7.181] [wifi0 best channel = 6, changed by apc because channel is inconsistent between driver and drm]
    elif "changed by" in msg:
        print(msg)
        try:
            band, best_channel, reason = re.findall(r"\[wifi(.*?) best channel = (.*?), changed by (.*?)\]", msg)[0]
            if band == "2":
                band = "5GHz High"
            if band == "1":
                band = "5GHz"
            if band == "0":
                band = "2.4GHz"
            else:
                pass 
            try:
                write_api.write(bucket, org, [{"measurement": "support_wlan_drm", "tags": {"AP_IPAddr": ipadd, "New_channel": best_channel, "Radio Band": band, "Changed by": reason}, "fields": {"count": 1}}])
            except UnboundLocalError as error:
                print(error)
                sys.exit()
            except Exception as error:
                print(error)
                pass
            info = "Preventive Maintenance Application - WLAN Stellar AP {} - Channel on Radio band {} changed to Channel {} reason ({}).".format(ipadd,band,best_channel,reason)
            send_message(info, jid)
        except UnboundLocalError as error:
            print(error)
            sys.exit()
        except IndexError as error:
            print(error)
            sys.exit()
    else:
        print("no pattern match - exiting script")
        sys.exit()
