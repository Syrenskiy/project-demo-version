from django.urls import path
from . import views

from django.utils.translation import gettext_lazy as _

app_name = 'payment'


urlpatterns = [
    path(_('procesar/'), views.PaymentProcessView.as_view(), name='process'),
    path(_('procesar/instrucciones-pago/'), views.PaymentInstructionsView.as_view(), name='payment_instructions'),
    path(_('confirmacion-pago/'), views.PaymentConfirmationView.as_view(), name='payment_confirmation'),
    path(_('completado/'), views.PaymentCompletedView.as_view(), name='completed'),
    path(_('cancelado/'), views.PaymentCanceledView.as_view(), name='canceled'),
    path('partial-payment-update/', views.UpdatePartialPaymentStatusView.as_view(), name='partial_payment_update'),
]
