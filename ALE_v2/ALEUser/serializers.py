from rest_framework import serializers
from .models import*
from django.contrib.auth.models import User

from django.core import exceptions
import django.contrib.auth.password_validation as validators

class UserDetail(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = ['username']

class UserTypesSerializer(serializers.ModelSerializer):
	class Meta:
		model = UserTypes
		fields = ['type_name']

class UserDetails(serializers.ModelSerializer):
	user_name = UserDetail(read_only="True")
	type_id = UserTypesSerializer(read_only="True")
	class Meta:
		model = Users
		fields = ['user_id', 'user_name', 'email', "type_id", "jid"]

class UserloginDetails(serializers.ModelSerializer):
	class Meta:
		model=User
		fields=['username','password']

# start - user api related things
class UserRegistrationSerializer(serializers.ModelSerializer):
	def validate_password(self, value):
		try:
			validators.validate_password(value)
		except exceptions.ValidationError as exc:
			raise serializers.ValidationError(str(exc))
		return value

	def create(self, validated_data):
		user = User.objects.create_user(username=validated_data['username'], password=validated_data['password'])
		return user

	class Meta:
		model = User
		fields = ['username', 'password']

class CustomUserRegistrationSerializer(serializers.ModelSerializer):	
	def create(self, validated_data):
		lower_email = validated_data['email'].lower()
		l_jid = validated_data['jid']
		if Users.objects.filter(email__iexact=lower_email).exists():
			raise serializers.ValidationError("Duplicate Email")

		custom_user = Users.objects.create(email=lower_email,jid=l_jid)
		return custom_user

	class Meta:
		model = Users
		fields = ['email','jid']

class CustomUserTypeSerializer(serializers.ModelSerializer):
	def create(self, validated_data):
		user_type = UserTypes.objects.get(type_name=validated_data['type_name'])
		return user_type

	class Meta:
		model = UserTypes
		fields = ['type_name']

# start-  serializers of decision/decision history 
class RuleNameSerializer(serializers.ModelSerializer):
	#function = serializers.CharField(source='rule_name')
	class Meta:
		model=Rules
		fields=['rule_name']

class DecisionListSerializer(serializers.ModelSerializer):
	rule_name=RuleNameSerializer(read_only="True",source='rule_id')
	class Meta:
		model=Decision_History
		fields=['ip_address','port','rule_name','decision']
# end-  serializers of decision/decision history 

# serialiser for rules

class ActionSerializer(serializers.ModelSerializer):
	action=serializers.CharField()
	#description=serializers.CharField()
	class Meta:
		model=Actions
		fields=['action']

class RuleCreateSerializer(serializers.ModelSerializer):
	create_rule=ActionSerializer(source='action_id')
	class Meta:
		model=Rules
		fields=['rule_name','create_rule','rule_description']

class RuleTypeListSerializer(serializers.ModelSerializer):
	rule_type=serializers.CharField(source='type_name')
	class Meta:
		model=RulesTypes
		fields=['rule_type']
		
class RuleListSerializer(serializers.ModelSerializer):
	action=ActionSerializer(source='action_id')
	rule_type=RuleTypeListSerializer(source='rule_type_id')
	class Meta:
		model=Rules
		fields=['rule_type','rules_id','rule_name','action','enabled','rule_description']

# serializers for statistics

class StatisticsRuleSerializer(serializers.ModelSerializer):
	#action=ActionRuleListSerializer(source='action_id')
	class Meta:
		model=Rules
		fields=['rule_name']#,'action']
class StatisticsSerializer(serializers.ModelSerializer):
	rule_name=StatisticsRuleSerializer(source='rule_id')
	result=serializers.CharField(source='actions_status')
	class Meta:
		model=Statistics
		fields=['timestamp','rule_name','result','details']

# Settings Serializer
class SettingsSerializer(serializers.ModelSerializer):
	class Meta:
		model = Settings_Value	
		fields = '__all__'