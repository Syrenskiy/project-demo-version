from django.apps import AppConfig


class PaymentConfig(AppConfig):
    verbose_name = 'Pago'
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payment'

    def ready(self):
        import payment.signals