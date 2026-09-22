from django.shortcuts import render, get_object_or_404
from .models import Priority, Task

def task_list(request):
    priorities = Priority.objects.all()
    tasks = Task.objects.all()
    return render(request, 'main/task/list.html', {'tasks': tasks, 'priorities': priorities})
