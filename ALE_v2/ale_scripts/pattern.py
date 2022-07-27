#!/usr/bin/env python3

import sys
from mysql.connector import connect
import itertools
from cryptography.fernet import Fernet
import logging
import os

path = os.path.dirname(__file__)
sys.path.insert(1,os.path.abspath(os.path.join(path,os.pardir)))
from alelog import alelog

# Database password decryption

db_key=b'gP6lwSDvUdI04A8fC4Ib8PXEb-M9aTUbeZTBM6XAhpI='
dbsecret_password=b'gAAAAABivYWTJ-2OZQW4Ed2SGRNGayWRUIQZxLckzahNUoYSJBxsg5YZSYlMdiegdF1RCAvG4FqjMXD-nNeX0i6eD7bdFV8BEw=='
fernet = Fernet(db_key)
db_password = fernet.decrypt(dbsecret_password).decode()

# end of decryption

database = connect(
		host="localhost",
		user="aletest",
		password=db_password,
		database="aledb"
		)
db = database.cursor()


def set_rule_pattern(pattern):
	global rule
	pattern = pattern.replace('"', '')
	rule = ''
	db.execute("SELECT * FROM ALEUser_rules")
	
	rules_list = db.fetchall()

	for _rule in rules_list:
		pattern_string = ""
		for value in pattern.split(";"):
			flag = True
			if value in ['and', 'or']:
				pattern_string += ' {0} '.format(value)
				continue

			if value not in _rule[1]:
				pattern_string += 'False'
				flag = False
				break
			
			if flag:
				pattern_string += 'True'

		if eval(pattern_string):
			rule = _rule
			break

	if rule == '':
		print('No Rule Found')
		sys.exit()
	
	if not rule[2]: 
		print("Rule not enabled")
		sys.exit(0)
		
def set_portnumber(portnum):
	global portnumber
	
	portnumber = portnum
	print('port-number -> ', portnumber)

def set_decision(ip_address, _decision = "1"):
	global decision
	user_decision = False
	
	if _decision == "2":
		decision = "Yes and Remember"
	elif _decision == "0":
		decision = "No"
	elif _decision == "4":
		decision = "Fake"
	else:
		decision = "Yes"

	if decision != "Fake":
		decision_history_query = 'SELECT * FROM ALEUser_decision_history WHERE rule_id_id = {0} AND ip_address = "{1}" AND port = "{2}";'.format(rule[0], ip_address, portnumber)
		db.execute(decision_history_query)
		decision_history = db.fetchall()
		# print('set_decision : decision history -> ', decision_history, decision_history_query, type(decision_history))

		if not rule[2]: 
			msg = 'DECISION : For IP Address {0} the Rule {1} was disabled.'.format(ip_address, rule[1])
			alelog.log_warning_module_script(msg)
			print("Rule not enabled")
			sys.exit(0)

		decision_query = 'SELECT * FROM ALEUser_decision WHERE decision = "{0}";'.format(decision)
		db.execute(decision_query)
		decision = db.fetchone()[0]
		# print('decision -> ', decision)
		
		for value in decision_history:
			if 'Yes and Remember' in value or 'No' in value:
				user_decision = True
				break
				
		if not (bool(decision_history) and user_decision):
			decision_history_insert_query = "INSERT INTO ALEUser_decision_history (ip_address, port, decision_id, rule_id_id) VALUES (%s, %s, %s, %s);"
			decision_history_insert_data = (ip_address, portnumber, decision, rule[0])
			
			msg = 'DECISION: For IP Address {0} and the Rulename {1}, the decision was set to {2}.'.format(ip_address, rule[1], decision)
			try:
				alelog.log_module_script(msg)
				db.execute(decision_history_insert_query, decision_history_insert_data)
				database.commit()
			except Exception as e:
				alelog.log_error_module_script(msg + ' Error while commiting in database: ' + str(e))
				database.rollback()
			
			print('decision saved')
			
def get_decision(ip_address):
	decision_history_query = 'SELECT DISTINCT decision_id FROM ALEUser_decision_history WHERE rule_id_id = {0} AND ip_address = "{1}" AND port = "{2}";'.format(rule[0], ip_address, portnumber)
	db.execute(decision_history_query)
	decision_history = db.fetchall()
	decision_history = list(itertools.chain(*decision_history))
	# print('get_decision : decision history -> ', decision_history, decision_history_query, type(decision_history))

	return decision_history

def mysql_save(runtime, ip_address, result, reason, exception):
	if exception:
		details = str(reason) + ', ' + str(exception) + ', ' + 'IP-Address: ' + str(ip_address) + ', ' + 'Port-Number: ' + str(portnumber)
	else:
		details = str(reason) + ', ' + 'IP-Address: ' + str(ip_address) + ', ' + 'Port-Number: ' + str(portnumber)
		
	# print('details -> ', details)
	statistics_insert_query = "INSERT INTO ALEUser_statistics (actions_status, details, timestamp, decision_id, rule_id_id) VALUES (%s, %s, %s, %s, %s);"
	statistics_insert_data = (result, details, runtime, decision, rule[0])
	
	try:
		alelog.log_module_script('STATISTICS:' + details)
		db.execute(statistics_insert_query, statistics_insert_data)
		database.commit()
	except Exception as e:
		alelog.log_error_module_script('STATISTICS:' +details + ' Error while commiting in database: ' + str(e))
		database.rollback()
	
	#if database.is_connected():
	#	db.close()
	#	database.close()		
	
	print('statistics updated')


