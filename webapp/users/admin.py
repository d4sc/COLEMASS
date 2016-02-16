from django.contrib import admin
from .models import *

# Register your models here.

class CardAdmin(admin.ModelAdmin):
    list_display = ('key', 'user', 'is_broken')

class UserDetailAdmin(admin.ModelAdmin):
    list_display = ('user', 'valid_key', 'is_absent', 'is_absent_since')

admin.site.register(Card, CardAdmin)
admin.site.register(UserDetail, UserDetailAdmin)
