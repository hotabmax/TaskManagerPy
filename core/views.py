from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, DeleteView, UpdateView, DetailView
from django.views import View
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Task
from .forms import TaskForm, StatusForm, BossUserCreateForm, EmployeeUserCreateForm
from django.urls import reverse_lazy

# Групповой миксин для проверки роли "Начальник"
class BossRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.groups.filter(name='Начальник').exists()

# Групповой миксин для проверки роли "Подчиненный"
class EmployeeRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.groups.filter(name='Подчиненный').exists()

# Главная страница - список задач (доступна всем авторизованным)
class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'core/task_list.html' 
    context_object_name = 'tasks' 
    def get_queryset(self): 
        qs = super().get_queryset() 
        if self.request.user.groups.filter(name='Подчиненный').exists():
            # Подчиненный видит только задачи, где он назначен исполнителем 
            return qs.filter(executor=self.request.user) 
            # Начальник видит все задачи
        return qs

# --- Детальный просмотр задачи ---
class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'core/task_detail.html'
    context_object_name = 'task'

    # Опционально: проверим, может ли пользователь видеть эту задачу
    def get_queryset(self):
        qs = super().get_queryset()
        # Начальник видит все задачи
        if self.request.user.groups.filter(name='Начальник').exists():
            return qs
        # Подчиненный видит только свои задачи
        if self.request.user.groups.filter(name='Подчиненный').exists():
            return qs.filter(executor=self.request.user)
        # Остальные авторизованные пользователи (если есть) не видят ничего
        return qs.none()

# Создание задачи (только для Начальника)
class TaskCreateView(LoginRequiredMixin, BossRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'core/task_form.html'
    success_url = reverse_lazy('task-list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Задача успешно создана!')
        return super().form_valid(form)

# Удаление задачи (только для Начальника)
class TaskDeleteView(LoginRequiredMixin, BossRequiredMixin, DeleteView):
    model = Task
    template_name = 'core/task_confirm_delete.html'
    success_url = reverse_lazy('task-list')

    def delete(self, request, *args, **kwargs):
        messages.info(self.request, 'Задача удалена.')
        return super().delete(request, *args, **kwargs)
    

# Изменение статуса (только для Подчиненного)
class TaskStatusUpdateView(LoginRequiredMixin, EmployeeRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        
        if task.executor != request.user:
            messages.error(request, 'Вы не можете менять статус чужой задачи.')
            return redirect('task-list')
        
        form = StatusForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Статус задачи обновлен.')
        else:
            messages.error(request, 'Ошибка обновления.')
        
        return redirect('task-list')

# --- Изменение задачи (Начальник) ---
class TaskUpdateView(LoginRequiredMixin, BossRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'core/task_update.html'
    success_url = reverse_lazy('task-list')

    def form_valid(self, form):
        messages.success(self.request, 'Задача успешно изменена.')
        return super().form_valid(form)


# --- Создание пользователя с ролью "Подчиненный" (только для Начальника) ---
class EmployeeUserCreateView(LoginRequiredMixin, BossRequiredMixin, CreateView):
    model = User
    form_class = EmployeeUserCreateForm
    template_name = 'core/employee_user_form.html'
    success_url = reverse_lazy('task-list')

    def form_valid(self, form):
        messages.success(self.request, 'Пользователь успешно создан и добавлен в роль "Подчиненный".')
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        initial['username'] = f"employee_{User.objects.count() + 1}"
        return initial


# --- Создание пользователя с ролью "Начальник" (только для Начальника) ---
class BossUserCreateView(LoginRequiredMixin, BossRequiredMixin, CreateView):
    model = User
    form_class = BossUserCreateForm
    template_name = 'core/user_form.html'
    success_url = reverse_lazy('task-list')

    def form_valid(self, form):
        messages.success(self.request, 'Пользователь успешно создан и добавлен в роль "Начальник".')
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        initial['username'] = f"boss_{User.objects.count() + 1}"
        return initial


class BossUserUpdateView(LoginRequiredMixin, BossRequiredMixin, UpdateView):
    model = User
    form_class = BossUserCreateForm
    template_name = 'core/user_form.html'
    success_url = reverse_lazy('task-list')

    def form_valid(self, form):
        messages.success(self.request, 'Данные пользователя успешно обновлены.')
        return super().form_valid(form)

    