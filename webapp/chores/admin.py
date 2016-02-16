from django.contrib import admin
from .models import *


class ChoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'assignee', 'assigned_time', 'nudges', 'last_nudge', 'active')

class CompletedChoreAdmin(admin.ModelAdmin):
    list_display = ('chore', 'user', 'date', 'nudges', 'confirmed')
    
class RefusedChoreAdmin(admin.ModelAdmin):
    list_display = ('chore', 'user', 'date', 'reason', 'confirmed')
    
class InfractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'chore', 'date', 'is_recent')
    
admin.site.register(Chore, ChoreAdmin)
admin.site.register(RecurringChore, ChoreAdmin)
admin.site.register(CompletedChore, CompletedChoreAdmin)
admin.site.register(Infraction, InfractionAdmin)
admin.site.register(RefusedChore, RefusedChoreAdmin)
