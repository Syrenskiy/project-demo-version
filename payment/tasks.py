from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from payment.models import PaymentConfirmation


@shared_task
def send_payment_confirmation_to_seller(payment_confirmation_id: int) -> int:
    """Task to send an email notification for a product suggestion"""
    payment_confirmation = PaymentConfirmation.objects.get(id=payment_confirmation_id)
    subject = 'Nueva Confirmación de Pago de Princess Castle'
    message = (
            '\nDetalles de la Confirmación:\n\n' +
            'Usuario: %(user)s\n' % {'user': payment_confirmation.user} +
            'Número del pedido: %(order_id)s\n' % {'order_id': payment_confirmation.order_id} +
            'Fecha de creación: %(created)s\n' % {'created': payment_confirmation.created}

    )
    to_email = settings.MAIN_SELLERS_EMAILS

    html_message = render_to_string('payment/emails/payment_confirmation_to_seller.html',
                                    {
                                        'payment_confirmation': payment_confirmation,
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
