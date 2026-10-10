from django import forms
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