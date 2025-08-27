from django import template
from django.core.cache import cache
from django.db.models import Count

from products.models import Category, Tag, Product

from typing import Any

register = template.Library()


@register.inclusion_tag('products/includes/list_categories.html')
def show_categories(cat_selected: int = 0) -> dict[str, Any]:
    """
    Retrieves all categories with the number of published products.
    Caches the result to improve performance.
    """

    categories = (Category.objects
                  .prefetch_related('translations')
                  .annotate(total=Count('products'))
                  .filter(products__is_published=Product.Status.PUBLISHED))
    return {'categories': categories, 'cat_selected': cat_selected}


@register.inclusion_tag('products/includes/list_tags.html')
def show_tags() -> dict[str, Any]:
    """
    Retrieves all tags with the count of associated published products.
    Caches the result for better performance.
    """

    tags = (Tag.objects
            .prefetch_related('translations')
            .annotate(total=Count("products"))
            .filter(products__is_published=Product.Status.PUBLISHED))

    return {'tags': tags}
