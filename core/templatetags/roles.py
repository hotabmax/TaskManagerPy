from django import template

register = template.Library()

@register.filter
def has_group(user, group_name):
    """
    Проверяет, состоит ли пользователь в группе с указанным именем.
    Использование в шаблоне: {% if user|has_group:"Начальник" %}
    """
    if user and user.is_authenticated:
        return user.groups.filter(name=group_name).exists()
    return False