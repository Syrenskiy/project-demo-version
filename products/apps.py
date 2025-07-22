from django.apps import AppConfig


class ProductsConfig(AppConfig):
    verbose_name = 'Productos'
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products'

    def ready(self):
        import products.signals
