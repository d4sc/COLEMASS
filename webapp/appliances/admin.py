from django.contrib import admin
from .models import *
from chores.admin import ChoreAdmin

# Register your models here.

class ApplianceAdmin(admin.ModelAdmin):
    list_display = ('name', 'hwid', 'is_in_use', 'last_user')

class ApplianceChoreAdmin(ChoreAdmin):
    list_display = ('appliance',) + ChoreAdmin.list_display

admin.site.register(Appliance, ApplianceAdmin)
admin.site.register(ApplianceChore, ApplianceChoreAdmin)
