from django import template

from decimal import Decimal


register = template.Library()


@register.filter(name='to')
def to(value: int, arg: int) -> range:
    """Creates a range from `value` to `arg` (inclusive)."""
    return range(value, arg + 1)


@register.filter
def floatformat_custom(value: float | Decimal) -> str:
    """Formats a number as a string with two decimal places."""
    return format(value, '.2f')
