import csv
import datetime

from django.contrib import admin
from django.forms import TextInput
from django.db import models
from django.http import HttpResponse
from django.urls import reverse
from django.utils.safestring import mark_safe
from parler.admin import TranslatableAdmin
from django.utils import timezone

from orders.models import OrderItem, Order, Delivery


class OrderItemInline(admin.TabularInline):
    """Inline admin interface for OrderItem, allowing items to be added directly within an Order."""
    model = OrderItem
    extra = 0
    formfield_overrides = {
        # Set the width for all CharField fields
        models.CharField: {'widget': TextInput(attrs={'size': '20'})},
    }


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin configuration for Order model, with display, filter, and action options
    for managing orders effectively.
    """
    list_display = ('id', 'user', 'order_detail', 'first_name', 'last_name', 'phone',
                    'delivery_formatted', 'created_formatted', 'updated_formatted',
                    'display_total', 'paid', 'display_partial_cost',
                    'paid_full', 'display_quantity')
    list_editable = ['paid', 'paid_full']
    actions = ['set_paid_full', 'export_to_csv']
    list_per_page = 10
    list_filter = ['created', 'updated', 'paid', 'partial_payment', 'delivery', 'user']
    search_fields = ['user', 'first_name', 'last_name', 'phone', 'delivery_formatted']
    inlines = [OrderItemInline]
    show_facets = admin.ShowFacets.ALWAYS
    fields = ('user', 'first_name', 'last_name', 'phone',
              'paid', 'partial_payment', 'paid_full',
              'delivery', 'address', 'created', 'updated',
              'coupon', 'discount')
    readonly_fields = ['user', 'address', 'coupon', 'discount', 'created', 'updated']
    save_on_top = True

    @admin.display(description='Cantidad')
    def display_quantity(self, order: Order) -> int:
        return order.get_total_product_quantity()

    @admin.display(description='Total')
    def display_total(self, order: Order) -> str:
        return f"${order.get_total_cost():.2f}"

    @admin.display(description='Creación')
    def created_formatted(self, order: Order) -> str:
        return timezone.localtime(order.created).strftime("%d.%m.%Y %H:%M")

    @admin.display(description='Actualización')
    def updated_formatted(self, order: Order) -> str:
        return timezone.localtime(order.updated).strftime("%d.%m.%Y %H:%M")

    @admin.display(description='Detalles')
    def order_detail(self, order: Order) -> SafeString:
        """Returns an admin link to view order details."""
        url = reverse('orders:admin_order_detail', args=[order.id])
        return mark_safe(f'<a href="{url}">Ver</a>')

    @admin.display(description='Pago Parcial')
    def display_partial_cost(self, order: Order) -> str:
        """Displays the cost with partial payment, if applicable."""
        if order.partial_payment:
            return f'${order.get_total_cost_with_partial_payment():.2f}'
        return "-"

    @admin.display(description='Entrega')
    def delivery_formatted(self, order: Order) -> str:
        """Formats delivery information; shows address if delivery is to home."""
        place = order.delivery.place
        if place == 'A Domicilio':
            return order.address
        return place

    @admin.action(description='Actualizar el Pago como Pago Completo')
    def set_paid_full(self, request, queryset: QuerySet[Order]) -> None:
        """Marks selected orders as fully paid."""
        count = queryset.update(paid_full=True)
        self.message_user(request, f'{count} artículos fueron cambiados como Pago Completo.')

    @admin.action(description='Exportar a CSV')
    def export_to_csv(self, request, queryset: QuerySet[Order]) -> HttpResponse:
        """
        Exports selected orders to CSV format, including all fields except for M2M and O2M relations.
        """
        opts = self.model._meta
        content_disposition = f'attachment; filename={opts.verbose_name}.csv'
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = content_disposition
        writer = csv.writer(response)
        # Include headers and data rows
        fields = [field for field in opts.get_fields() if not field.many_to_many and not field.one_to_many]
        # Write a first row with header information
        writer.writerow([field.verbose_name for field in fields])
        # Write data rows
        for obj in queryset:
            data_row = []
            for field in fields:
                value = getattr(obj, field.name)
                if isinstance(value, datetime.datetime):
                    value = value.strftime('%d/%m/%Y')
                data_row.append(value)
            writer.writerow(data_row)
        return response


@admin.register(Delivery)
class DeliveryAdmin(TranslatableAdmin):
    """Admin interface for managing Delivery options."""
    list_display = ['id', 'place', 'order_field']
    list_display_links = ['id', 'place']
    list_editable = ['order_field']
