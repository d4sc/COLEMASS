from django.contrib import admin
from .models import *

# Register your models here.

class DishAdmin(admin.ModelAdmin):
    list_display = ('title', 'tag', 'isTakenOut', 'assignee', 'update_time')

class DishLogAdmin(admin.ModelAdmin):
    list_display = ('dish', 'taken_by', 'taken_time', 'returned_by', 'returned_time')

admin.site.register(ItemTracker)
admin.site.register(Hardware)
admin.site.register(DishChore)
admin.site.register(DishLog, DishLogAdmin)
admin.site.register(Dish, DishAdmin)
admin.site.register(UnregisteredDish)