from django import forms
from django.contrib.auth.models import User, Group
from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'priority', 'executor']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Введите название задачи'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-input', 'placeholder': 'Опишите задачу...'}),
            'priority': forms.Select(attrs={'class': 'form-input'}),
            'executor': forms.Select(attrs={'class': 'form-input'}),
        }


class StatusForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['status']
        widgets = {
            'status': forms.Select(choices=[(True, 'Готово'), (False, 'Не готово')])
        }


class BaseUserCreateForm(forms.ModelForm):
    """Базовая форма для создания/редактирования пользователя с назначением роли"""
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-input'}),
    )
    password_confirm = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={'class': 'form-input'}),
    )
    role_name = 'Роль'  # Переопределяется в подклассах

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'readonly': True}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['username'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Пароли не совпадают')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            group, _ = Group.objects.get_or_create(name=self.role_name)
            user.groups.add(group)
        return user


class BossUserCreateForm(BaseUserCreateForm):
    """Форма для создания/редактирования пользователя с ролью 'Начальник'"""
    role_name = 'Начальник'


class EmployeeUserCreateForm(BaseUserCreateForm):
    """Форма для создания пользователя с ролью 'Подчиненный'"""
    role_name = 'Подчиненный'