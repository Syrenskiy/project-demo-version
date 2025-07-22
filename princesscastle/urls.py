"""
URL configuration for princesscastle project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from orders import views as orders_views
from products.sitemaps import sitemaps
from products.views import Custom404View, UpdatePriceView, PrivacyPolicyView

from django.utils.translation import gettext_lazy as _

schema_view = get_schema_view(
    openapi.Info(
        title="Princess Castle API",
        default_version='v1',
        description="API documentation for the project",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email=settings.EMAIL_HOST_USER),
        license=openapi.License(name="BSD License"),
    ),
    public=False,
    permission_classes=[permissions.IsAdminUser],
)

urlpatterns = i18n_patterns(
    path('pincheleches/', admin.site.urls),
    path(_('carrito/'), include('cart.urls', namespace="cart")),
    path(_('pedidos/'), include('orders.urls', namespace="orders")),
    path(_('pago/'), include('payment.urls', namespace="payment")),
    path(_('cupones/'), include('coupons.urls', namespace="coupons")),
    path(_('usuarios/'), include('users.urls', namespace="users")),
    path('rosetta/', include('rosetta.urls')),
    path('', include('products.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
)

urlpatterns += [
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('orders/get-delivery-cost/<int:delivery_id>/', orders_views.GetDeliveryCostView.as_view(),
         name='get_delivery_cost'),
    path('update-price/', UpdatePriceView.as_view(), name='update_price'),
    path('api/', include('products.api.urls', namespace='api')),

    path('privacy-policy/', PrivacyPolicyView.as_view(), name='privacy_policy'),

    # Swagger URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]

handler404 = Custom404View.as_view()

admin.site.site_header = 'Administración de Princess Castle'
admin.site.site_title = 'Princesscastle Administration'
