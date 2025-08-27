from django.contrib import admin
from django.utils.safestring import mark_safe, SafeString
from django.utils import timezone

from payment.models import PaymentConfirmation


@admin.register(PaymentConfirmation)
class PaymentConfirmationAdmin(admin.ModelAdmin):
    """Admin configuration for PaymentConfirmation model."""
    list_display = ('user', 'order_id', 'display_image', 'verified',
                    'created_formatted', 'updated_formatted')
    list_display_links = ['user']
    list_editable = ['verified']
    list_per_page = 10
    fields = ['user', 'order_id', 'display_image', 'verified']
    readonly_fields = ['display_image', 'created_formatted', 'updated_formatted']

    @admin.display(description='Imágen')
    def display_image(self, payment: PaymentConfirmation) -> SafeString | None:
        """Displays a thumbnail image in the admin interface."""
        if payment.image:
            return mark_safe(f"<a href='{payment.image.url}'><img src='{payment.image.url}' alt='{payment.image.name}' width='50'></a>")

    @admin.display(description='Creado')
    def created_formatted(self, obj: PaymentConfirmation) -> str:
        return timezone.localtime(obj.created).strftime("%d.%m.%Y %H:%M")

    @admin.display(description='Actualizado')
    def updated_formatted(self, obj: PaymentConfirmation) -> str:
        return timezone.localtime(obj.updated).strftime("%d.%m.%Y %H:%M")
