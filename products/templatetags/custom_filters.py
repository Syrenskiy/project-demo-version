from django import template


register = template.Library()


@register.filter(name='to')
def to(value, arg):
    return range(value, arg + 1)


@register.filter
def floatformat_custom(value):
    return format(value, '.2f')
