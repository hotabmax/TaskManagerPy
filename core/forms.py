from django import forms
from .models import Task

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'priority', 'executor']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'executor': forms.Select(attrs={'class': 'form-control'}),
        }

class StatusForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['status']
        widgets = {
            'status': forms.Select(choices=[(True, 'Готово'), (False, 'Не готово')])
        }