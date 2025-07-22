from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "web",
    ".ngrok-free.app",
    ".ngrok.io",
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'django_extensions',
    'products.apps.ProductsConfig',
    'users.apps.UsersConfig',
    'orders.apps.OrdersConfig',
    'cart.apps.CartConfig',
    'payment.apps.PaymentConfig',
    'coupons.apps.CouponsConfig',
    'debug_toolbar',
    'social_django',
    'rosetta',
    'parler',
    'redisboard',
    'rest_framework',
    'rest_framework.authtoken',
    'djoser',
    'drf_yasg',
    'storages',
    'turnstile',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB'),
        'USER': config('POSTGRES_USER'),
        'PASSWORD': config('POSTGRES_PASSWORD'),
        'HOST': config('POSTGRES_HOST'),
        'PORT': config('POSTGRES_PORT'),
    }
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATIC_ROOT = BASE_DIR / 'static'

MEDIA_ROOT = BASE_DIR / 'media'

STATIC_URL = '/static/'

MEDIA_URL = '/media/'

EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST = "smtp.gmail.com"
EMAIL_HOST_USER = config('EMAIL_HOST_USER_OLD')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD_OLD')

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SERVER_EMAIL = EMAIL_HOST_USER
EMAIL_ADMIN = EMAIL_HOST_USER

ADMINS_EMAIL = config('ADMINS_EMAIL_DEV', cast=Csv())
MAIN_SELLERS_EMAILS = config('ADMINS_EMAIL_DEV', cast=Csv())
SELLERS_EMAILS = config('ADMINS_EMAIL_DEV', cast=Csv())

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # Disable existing loggers

    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },

    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'project.log'),
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },

    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'api': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

DOMAIN = config('DOMAIN_DEV')

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: True,
    'INTERCEPT_REDIRECTS': False,
}

CSRF_TRUSTED_ORIGINS = [
    'https://7777-7777-2f0-8777-fe7d-7ddd-99b5-7672-bb27.ngrok-free.app',
]
