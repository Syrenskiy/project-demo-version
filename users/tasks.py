from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

from django.conf import settings
from django.template.loader import render_to_string

from django.utils.translation import gettext_lazy as _


@shared_task
def send_registration_email(user_email):
    """Celery task to send a welcome email to a newly registered user."""
    subject = 'Princess Castle'
    message = _('Registro exitoso.\n\nBienvenido(a) a la familia Princess Castle!')
    html_message = render_to_string('users/emails/welcome.html')
    return send_mail(subject, message, settings.EMAIL_HOST_USER,
                     [user_email], fail_silently=True, html_message=html_message)
