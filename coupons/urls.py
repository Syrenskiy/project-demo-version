from django.urls import path

from coupons import views

app_name = 'coupons'

urlpatterns = [
    path('apply/', views.CouponApplyView.as_view(), name='apply'),
]
