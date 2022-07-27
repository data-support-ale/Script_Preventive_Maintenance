from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(UserTypes)
admin.site.register(Users)
admin.site.register(Settings_Value)
admin.site.register(RulesTypes)
admin.site.register(Actions)
admin.site.register(Rules)
admin.site.register(Decision)
admin.site.register(Statistics)
admin.site.register(Decision_History)
