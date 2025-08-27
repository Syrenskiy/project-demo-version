from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from parler.models import TranslatableModel, TranslatedFields, TranslationDoesNotExist

from coupons.models import Coupon

from django.utils.translation import gettext_lazy as _


class Order(models.Model):
    """
    Model representing a customer's order, including user, delivery, payment, and discount information.
    Calculates order totals and manages partial payment status.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
                             related_name='orders', verbose_name=_('Usuario'))
    first_name = models.CharField(max_length=50, verbose_name=_('Nombre'))
    last_name = models.CharField(max_length=50, verbose_name=_('Apellido'))
    email = models.EmailField(verbose_name=_('Correo electrónico'))
    phone = models.CharField(max_length=50, verbose_name=_('Teléfono'))
    address = models.CharField(max_length=150, verbose_name=_('Dirección'))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Creado'))
    updated = models.DateTimeField(auto_now=True, verbose_name=_('Actualizado'))
    delivery = models.ForeignKey('Delivery', on_delete=models.DO_NOTHING,
                                 related_name='orders', verbose_name=_('Entrega'))
    paid = models.BooleanField(default=False, verbose_name=_('Pagado'))
    coupon = models.ForeignKey(Coupon, related_name='orders', null=True, blank=True,
                               on_delete=models.SET_NULL, verbose_name=_('Cupón'))
    discount = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)],
                                   verbose_name=_('Descuento'))
    partial_payment = models.BooleanField(default=False, verbose_name=_('Pago Parcial'))
    paid_full = models.BooleanField(default=False, verbose_name=_('Pagado Completo'))
    language = models.CharField(max_length=3, default=settings.LANGUAGE_CODE)

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created']),
        ]
        verbose_name = _('Orden')
        verbose_name_plural = _('Ordenes')

    def __str__(self):
        return _('Orden %(order_id)s') % {'order_id': self.id}

    def get_total_product_quantity(self) -> int:
        """Calculate the total quantity of products in the order."""
        return sum(item.product_quantity for item in self.items.all())

    def get_total_cost(self) -> Decimal:
        """Calculate the total cost of the order, including discounts and delivery cost."""
        total_cost = self.get_total_cost_before_discount() - self.get_discount() + self.delivery.cost
        return total_cost

    def get_total_cost_before_discount(self) -> Decimal:
        """Calculate the total cost of items in the order before applying discounts."""
        return sum(item.get_cost() for item in self.items.all())

    def get_discount(self) -> Decimal:
        """Calculate the discount amount for the order."""
        if self.discount:
            total_cost = self.get_total_cost_before_discount()
            return total_cost * (self.discount / Decimal(100))
        return Decimal(0)

    def get_total_cost_with_partial_payment(self) -> Decimal:
        """Calculate the cost of the order if only a partial payment is made."""
        return self.get_total_cost() / 2

    def send_payment_instructions_email(self) -> None:
        """Starts background sending of an email with payment instructions."""
        from orders.tasks import send_payment_instructions
        send_payment_instructions.delay(self.id)

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to send order confirmation emails upon payment updates."""
        previous_order = None
        if self.pk:
            previous_order = Order.objects.get(pk=self.pk)

        super().save(*args, **kwargs)

        # Send emails if payment status changed
        if previous_order:
            try:
                if not previous_order.paid and self.paid:
                    from orders.tasks import send_order_confirmation_to_client, send_order_confirmation_to_seller
                    send_order_confirmation_to_client.delay(self.id)
                    send_order_confirmation_to_seller.delay(self.id)

                if not previous_order.paid_full and self.paid_full:
                    from orders.tasks import send_comment_invitation_to_client
                    send_comment_invitation_to_client.delay(self.id)

            except Exception as e:
                import logging
                logging.error(f'Error al mandar email: {e}')


class OrderItem(models.Model):
    """Model representing an item in an order, linked to a product with specific attributes."""
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='items', verbose_name=_('Orden'))
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE,
                                related_name='items', verbose_name=_('Producto'))
    color = models.CharField(max_length=30, verbose_name=_('Color'))
    quantity = models.CharField(max_length=10, null=True, blank=True, verbose_name=_('Piezas'))
    size = models.CharField(max_length=30, null=True, blank=True, verbose_name=_('Talla'))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Precio'))
    product_quantity = models.PositiveIntegerField(default=1, verbose_name=_('Cantidad'))
    commented = models.BooleanField(default=False, verbose_name=_('Comentado'))

    def __str__(self):
        return str(self.id)

    def get_cost(self) -> Decimal:
        """Calculate the total cost for this order item."""
        return self.price * self.product_quantity


class Delivery(TranslatableModel):
    """
    Model for delivery options available for orders, with associated translations for delivery location.
    """
    translations = TranslatedFields(
        place=models.CharField(max_length=50, verbose_name=_('Lugar de Entrega'))
    )
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Precio'))
    order_field = models.PositiveIntegerField(default=0, verbose_name='Campo de Orden')

    class Meta:
        verbose_name = _('Entrega')
        verbose_name_plural = _('Entregas')

    def __str__(self):
        try:
            return self.place
        except TranslationDoesNotExist:
            return ''
