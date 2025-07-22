from django.conf import settings
from django.db import models

from django.utils.translation import gettext_lazy as _


class PaymentConfirmation(models.Model):
    """Model representing a Payment Confirmation sent by the buyer."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
                             verbose_name=_('Usuario'))
    order_id = models.CharField(max_length=15, verbose_name=_('Número de pedido'))
    image = models.ImageField(upload_to='images/orders/proof_of_payment/',
                              blank=True, null=True, verbose_name=_('Comprobante de pago'))
    verified = models.BooleanField(default=False, verbose_name=_('Verificado'))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Creado'))
    updated = models.DateTimeField(auto_now=True, verbose_name=_('Actualizado'))

    def __str__(self):
        return f'Confirmación de pago de usuario {self.user}, con el número de pedido {self.order_id}'
