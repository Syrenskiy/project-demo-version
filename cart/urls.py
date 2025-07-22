from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.CartDetailView.as_view(), name='cart_detail'),
    path('add/<int:product_id>/<slug:color_slug>/', views.CartAddView.as_view(), name='cart_add'),
    path('subtract/<int:product_id>/<slug:color_slug>/', views.CartSubtractView.as_view(), name='cart_subtract'),
    path('remove/<int:product_id>/<slug:color_slug>/', views.CartRemoveView.as_view(), name='cart_remove'),
]
