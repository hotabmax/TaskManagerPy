from django.contrib import admin

from .models import Priority, Task

@admin.register(Priority)
class PriorityAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['name', 'priority', 'description', 'created',
                    'updated', 'completed' ]
    list_filter = ['priority', 'created','updated', 'completed']
    list_editable = ['priority', 'completed']
