from django.urls import path, include, re_path
from rest_framework import routers

from . import views

app_name = 'products'

# Register API routes
router = routers.DefaultRouter()
router.register('products', views.ProductViewSet)
router.register('categories', views.CategoryViewSet)
router.register('tags', views.TagViewSet)

urlpatterns = [
    path('v1/auth/', include('djoser.urls')),  # Authentication endpoints (Djoser library)
    re_path(r'^auth/', include('djoser.urls.authtoken')),  # Token-based auth endpoints
    path('v1/', include(router.urls)),  # API version 1 routes
]
