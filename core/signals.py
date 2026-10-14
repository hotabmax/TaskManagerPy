from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group


@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    """Автоматическое создание групп при запуске миграций."""
    if sender.name != 'core':
        return

    groups_data = [
        {'name': 'Начальник'},
        {'name': 'Подчиненный'},
    ]

    for group_data in groups_data:
        Group.objects.get_or_create(**group_data)
