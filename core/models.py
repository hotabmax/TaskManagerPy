from django.db import models
from django.db.models import Case, When, IntegerField
from django.contrib.auth.models import User


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('High', 'Высокий'),
        ('Medium', 'Средний'),
        ('Low', 'Низкий'),
    ]

    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True, null=True)
    priority = models.CharField('Приоритет', max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    status = models.BooleanField('Готово', default=False)
    created_at = models.DateTimeField('Время создания', auto_now_add=True)
    updated_at = models.DateTimeField('Время изменения', auto_now=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор', related_name='created_tasks')
    executor = models.ForeignKey(User, on_delete=models.SET_NULL, verbose_name='Исполнитель', related_name='assigned_tasks', null=True, blank=True)

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = [
                Case( 
                When(status=False, then=0), 
                When(status=True, then=1), 
                output_field=IntegerField(), )
                ,
                Case(
                When(priority='High', then=0),
                When(priority='Medium', then=1),
                When(priority='Low', then=2),
                output_field=IntegerField(),)
                ,'-created_at']

    def __str__(self):
        return self.title

