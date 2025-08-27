from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from products.models import ProductSuggestion


@shared_task
def send_product_suggestion_notification(suggestion_id: int) -> int:
    """Task to send an email notification for a product suggestion"""
    suggestion = ProductSuggestion.objects.get(id=suggestion_id)
    subject = 'Nueva Propuesta de Princess Castle'
    message = suggestion.description
    to_email = settings.MAIN_SELLERS_EMAILS

    html_message = render_to_string('products/emails/send_product_suggestion_notification.html',
                                    {
                                        'suggestion': suggestion,
                                        'domain': settings.DOMAIN,
                                        'admin_panel': settings.ADMIN_PANEL,
                                    })
    return send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        to_email if isinstance(to_email, list) else [to_email],
        html_message=html_message,
    )
