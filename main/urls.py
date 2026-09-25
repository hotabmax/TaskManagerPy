from django.urls import path
from . import views

app_name = 'main'
urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('<int:id>', views.task_details, name='task_details')
]