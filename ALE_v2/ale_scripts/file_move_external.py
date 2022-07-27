# ***************************************************************************************************************************************************#
# Script for copying log to external device    
# if used space of local drive is greater than 80% then the script check and following tasks
# check for external device have free space or available, script will copy log file to external device and will delete the log file in local drive
# if device is full or not available, script will delete the log file in local drive will be deleted
# Note: Need to give values for following ariables
# original : actual source of log path with filename
# target : destination path of external device with filename
# hdd_details : local drive name or local drive path
# sample values provided, can be changed if needed

# Note: - If external hdd or target path is not available or external hdd
#         dont have enough size to store, the current log in the original path would be deleted.       
#       - Sample values provided, can be changed if needed
#       - Must have external drive connected with write permissions
# ****************************************************************************************************************************************************# 

import psutil
import shutil
import os

# source log filename with path with need to be moved to external device
original = [r'/usr/logs/user.log',r'/usr/logs/next.log'] 
# destination path to where the log files need to moved.
target = r'/newmount/logs_backup/'

hdd_details = psutil.disk_usage("/")
print(hdd_details.percent)
if hdd_details.percent>80:
   for logfile in original:
      try:
         shutil.copy(logfile, target)
         os.remove(logfile)
      except:
         os.remove(logfile)