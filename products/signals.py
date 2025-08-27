from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import Comment, ProductSuggestion
from .tasks import send_product_suggestion_notification
from .utils import generate_cache_key


@receiver(post_save, sender=Comment)
def clear_product_cache(sender, instance, **kwargs):
    """Clears the product cache when a new comment is created to ensure fresh data."""
    product_id = instance.product.id
    cache_key = generate_cache_key('product', product_id)
    cache.delete(cache_key)


@receiver(post_save, sender=ProductSuggestion)
def send_notification(sender, instance, created: bool, **kwargs):
    """Triggers the email notification task when a ProductSuggestion is created."""
    if created:
        send_product_suggestion_notification.delay(instance.id)
