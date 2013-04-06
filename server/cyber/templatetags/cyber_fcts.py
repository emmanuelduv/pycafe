from django import template
register = template.Library()
@register.filter(name='sub')
def sub(value, arg):
    return value - arg
