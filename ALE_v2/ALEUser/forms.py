from django.forms import ModelForm
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import *

class UserCreate(UserCreationForm):
	class Meta:
		model=User
		fields=['username','email','password1','password2']

class UserDetails(ModelForm):
	class Meta:
		model=Users 
		fields='__all__'		