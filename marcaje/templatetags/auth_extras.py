from django import template

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

@register.filter(name='add_class')
def add_class(field, css):
    return field.as_widget(attrs={"class": css})
