from django import template

from decimal import Decimal



register = template.Library()


@register.filter
def multiply(value: int | float | Decimal, arg: int | float) -> float:
    return float(value) * arg
