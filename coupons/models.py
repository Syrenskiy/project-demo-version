from django.utils import timezone

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from django.utils.translation import gettext_lazy as _


class Coupon(models.Model):
    """
    Model representing a discount coupon. Each coupon has a unique code,
    a date range in which it is valid, a discount percentage, and an active status.
    """
    code = models.CharField(max_length=50, unique=True)
    valid_from = models.DateTimeField(verbose_name='Válido desde')
    valid_to = models.DateTimeField(verbose_name='Válido hasta')
    discount = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Valor porcentual (de 0 a 100)'
    )
    remaining_uses = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='Usos restantes',
        help_text='Número de veces que se puede usar este cupón. Déjelo vacío para uso ilimitado.'
    )
    active = models.BooleanField()

    class Meta:
        verbose_name = _('Cupón')
        verbose_name_plural = _('Cupones')

    def use(self):
        """
        Applies the coupon if it has remaining uses.
        Returns True if the coupon was successfully applied, False otherwise.
        """
        if self.remaining_uses is not None:
            if self.remaining_uses == 0:
                return False

            self.remaining_uses -= 1
            self.save(update_fields=['remaining_uses'])

        return True

    def is_valid(self):
        """Checks if the coupon is currently valid based on date range and active status."""
        now = timezone.now()
        return self.valid_from <= now <= self.valid_to and self.active

    def __str__(self):
        return self.code

