from django.urls import path

from . import views

from django.utils.translation import gettext_lazy as _

app_name = 'orders'

urlpatterns = [
    path(_('crear/'), views.OrderCreateView.as_view(), name='order_create'),
    path('admin/order/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
]
