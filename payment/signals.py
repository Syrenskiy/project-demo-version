from django.db.models.signals import post_save
from django.dispatch import receiver

from payment.models import PaymentConfirmation
from .tasks import send_payment_confirmation_to_seller


@receiver(post_save, sender=PaymentConfirmation)
def send_notification(sender, instance, created, **kwargs):
    """Triggers the email notification task when a ProductSuggestion is created."""
    if created:
        send_payment_confirmation_to_seller.delay(instance.id)
