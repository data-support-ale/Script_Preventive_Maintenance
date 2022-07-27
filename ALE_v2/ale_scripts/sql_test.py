#!/usr/bin/env python3

import json
import sys
from mysql.connector import connect
from cryptography.fernet import Fernet
import os
import json
from support_tools_OmniSwitch import get_credentials
import requests

path = os.path.dirname(__file__)
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

# Database password decryption

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

""" settings = {
    'switch_user': "switch_user", 
    'switch_password': "switch_password",
    'mails': "mails",
    'jid1': "jid1",
    'jid2': "jid2",
    'jid3': "jid3",
    'ip_server': "ip_server",
    'login_AP': "login_AP",
    'pass_AP': "pass_AP",
    'tech_pass': "tech_pass",
    'random_id': "random_id",
    'company': "company",
    'room_id': "room"
}

settings_str = json.dumps(json.dumps(settings))
subject = (
    "NBD Preventive Maintenance - There is a new Setup, End Customer: \"{0}\"").format("company")
body = "Attached to this message the configuration file, please setup the VNA accordingly"
url = "https://vna.preprod.omniaccess-stellar-asset-tracking.com/api/flows/NBDNotif_Setup_File"
headers = {
    'Content-type': "text/plain",
    'Content-Disposition': "attachment;filename=settings.conf",
    'jid1': '{0}'.format("a3f42fb284954cc38eed1006b1e775fd@openrainbow.com"),
    'toto': '{0}'.format(subject),
    'tata': '{0}'.format(body)
}
# ALE_Script.conf is attached in the ALE Admin Rainbow bubble

file = {'file': ('settings.conf', settings_str)}
response = requests.post(url, files=file, headers=headers)
print(response) """

""" query = "SELECT COUNT(*) FROM ALEUser_settings_value"
db.execute(query)

result = db.fetchall()[0][0]
print(result)
 """


""" query = "SELECT * FROM ALEUser_settings_value"
db.execute(query)

result = json.loads(db.fetchall()[1][2])
print(result) """
# Insert a row of data
"""switch_user, switch_password, mails, jid1, jid2, jid3, ip_server, login_AP, pass_AP, tech_pass,  company, room_id = get_credentials()
room_id = get_credentials("room_id")
settings = {
    'switch_user': switch_user, 
    'switch_password': switch_password,
    'mails': mails,
    'jid1': jid1,
    'jid2': jid2,
    'jid3': jid3,
    'ip_server': ip_server,
    'login_AP': login_AP,
    'pass_AP': pass_AP,
    'tech_pass': tech_pass,
    'random_id': 
    'company': company,
    'room_id': room_id
}

settings_str = json.dumps(json.dumps(settings))
query = "INSERT INTO ALEUser_settings_value VALUES (2,'SETTINGS'," + settings_str +  ")"
db.execute(query)

# Save (commit) the changes
database.commit()"""

url = "http://10.130.7.178:8000/api/login"
payload = json.dumps({
  "username": "jonathan.trebaol@al-enterprise.com",
  "password": "OmniVista2500*"
})
headers = {
  'Content-Type': 'application/json'
}
response = requests.request("POST", url, headers=headers, data=payload)
csrftoken = response.cookies["csrftoken"]
cookies = response.headers["Set-Cookie"]

url = "http://10.130.7.178:8000/api/decisions/"

payload={}
headers = {
  'X-CSRFToken': csrftoken,
  'Cookie': cookies
}


query = "SELECT * FROM ALEUser_decision_history"
db.execute(query)
decisions = db.fetchall()

_ip = "192.168.80.81"
_port = "1/1/10"
for id, ip, port, decis, rule in decisions:
    if ip==_ip and port==_port:
        response = requests.request("DELETE", url+str(id), headers=headers, data=payload)
        print(response.text)
# We can also close the connection if we are done with it.
# Just be sure any changes have been committed or they will be lost.
database.close()