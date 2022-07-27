from django.db import models
from django.contrib.auth.models import User
from django.db.models import Model

class UserTypes(models.Model):
	type_id=models.BigAutoField(primary_key=True)
	type_name=models.CharField(max_length=25)

	def __str__(self):
		return str(self.type_id)

class Users(models.Model):
	user_id=models.BigAutoField(primary_key=True)
	user_name=models.OneToOneField(User,null=True,on_delete=models.CASCADE)
	type_id=models.ForeignKey(UserTypes,null=True,on_delete=models.CASCADE)
	email=models.EmailField(max_length=255)
	jid=models.EmailField(max_length=255,null=True)
	#password=models.ForeignKey(UserTypes,on_delete=models.CASCADE)


	def __str__(self):
		return str(self.user_name)

class Settings_Value(models.Model):
	id=models.BigAutoField(primary_key=True)
	name=models.CharField(max_length=255)
	value=models.JSONField()

	def __str__(self):
		return str(self.id)

class RulesTypes(models.Model):
	rule_type_id=models.BigAutoField(primary_key=True)
	type_name=models.CharField(max_length=50)
	
	def __str__(self):
		return str(self.rule_type_id)

class Actions(models.Model):
	action_id=models.BigAutoField(primary_key=True)
	action=models.CharField(max_length=255)
	description=models.TextField()
	script_path=models.CharField(max_length=255)

	def __str__(self):
		return str(self.action_id)

class Rules(models.Model):
	rules_id=models.BigAutoField(primary_key=True)
	rule_name=models.CharField(max_length=255)
	rule_type_id=models.ForeignKey(RulesTypes,on_delete=models.CASCADE)
	action_id=models.ForeignKey(Actions,on_delete=models.CASCADE)
	enabled=models.BooleanField()
	timeout=models.IntegerField()
	rule_description=models.TextField(null=True)
	
	def __str__(self):
		return str(self.rules_id)

class Decision(models.Model):
	decision=models.CharField(max_length=50,primary_key=True)

	def __str__(self):
		return self.decision

class Statistics(models.Model):
	id=models.BigAutoField(primary_key=True)
	rule_id=models.ForeignKey(Rules,on_delete=models.CASCADE)
	actions_status=models.CharField(max_length=50)
	decision=models.ForeignKey(Decision,on_delete=models.CASCADE)
	details=models.TextField()
	timestamp=models.DateTimeField()

	def __str__(self):
		return str(self.id)

class Decision_History(models.Model):
	id=models.BigAutoField(primary_key=True)
	rule_id=models.ForeignKey(Rules,on_delete=models.CASCADE)
	#ip_address=models.CharField(max_length=50)
	ip_address=models.GenericIPAddressField()
	port=models.CharField(max_length=50)
	decision=models.ForeignKey(Decision,on_delete=models.CASCADE)

	def __str__(self):
		return str(self.id)


