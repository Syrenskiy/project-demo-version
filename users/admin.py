from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from orders.models import Order
from .models import User
from django.utils import timezone


@admin.register(User)
class UserAdmin(UserAdmin):
    """Customize the admin interface for the User model, displaying specific fields."""
    list_display = ('username', 'email_formatted', 'date_joined_formatted',
                    'last_login_formatted', 'count_orders_paid', 'is_active')
    list_display_links = ['username', 'email_formatted']
    list_editable = ['is_active']

    @admin.display(description='Correo Electrónico')
    def email_formatted(self, user: User):
        """Display user's email in the list view."""
        return user.email

    @admin.display(description='Fecha de creación')
    def date_joined_formatted(self, user: User):
        """Format and display the date the user joined."""
        return timezone.localtime(user.date_joined).strftime("%d.%m.%Y %H:%M")

    @admin.display(description='Último ingreso')
    def last_login_formatted(self, user: User):
        """Format and display the user's last login date."""
        return timezone.localtime(user.last_login).strftime("%d.%m.%Y %H:%M") if user.last_login else '-'

    @admin.display(description='Pedidos')
    def count_orders_paid(self, user: User):
        """Display total orders paid for the user."""
        return Order.objects.filter(user=user, paid_full=True).count()
