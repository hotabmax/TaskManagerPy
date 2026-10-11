from django.urls import path
from . import views

urlpatterns = [
    path('', views.TaskListView.as_view(), name='task-list'),
    path('<int:pk>/', views.TaskDetailView.as_view(), name='task-detail'),
    path('create/', views.TaskCreateView.as_view(), name='task-create'),
    path('edit/<int:pk>/', views.TaskUpdateView.as_view(), name='task-update'),
    path('delete/<int:pk>/', views.TaskDeleteView.as_view(), name='task-delete'),
    path('status/<int:pk>/', views.TaskStatusUpdateView.as_view(), name='task-status'),
    
    # Управление пользователями - Начальник
    path('users/boss/create/', views.BossUserCreateView.as_view(), name='boss-user-create'),
    path('users/edit/<int:pk>/', views.BossUserUpdateView.as_view(), name='boss-user-update'),
    
    # Управление пользователями - Подчиненный
    path('users/employee/create/', views.EmployeeUserCreateView.as_view(), name='employee-user-create'),
]