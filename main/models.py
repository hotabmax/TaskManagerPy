from django.db import models

class Priority(models.Model):
    name = models.CharField(max_length=100, db_index=True)

    class Meta:
        verbose_name_plural = "Приоритеты"
        verbose_name = "Приоритет"
        ordering = ('name',)

    def __str__(self):
        return self.name

class Task(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    priority = models.ForeignKey(Priority, related_name='tasks', on_delete=models.PROTECT)
    description = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Задачи"
        verbose_name = "Задача"
        ordering = ('priority',)

    def __str__(self):
        return self.name