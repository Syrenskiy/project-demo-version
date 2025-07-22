from .base import *

from django.core.files.storage import default_storage
from princesscastle.settings.storages import MediaStorage

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Security
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

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
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ADMINS_EMAIL = config('ADMINS_EMAIL', cast=Csv())
MAIN_SELLERS_EMAILS = config('MAIN_SELLERS_EMAILS', cast=Csv())
SELLERS_EMAILS = config('SELLERS_EMAILS', cast=Csv())

ADMINS = [
    ('Iglesias J', ADMINS_EMAIL)
]

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('RDS_DB'),
        'USER': config('RDS_USER'),
        'PASSWORD': config('RDS_PASSWORD'),
        'HOST': config('RDS_ENDPOINT'),
        'PORT': config('RDS_PORT'),
        'OPTIONS': {
            'sslmode': 'require',
            'sslrootcert': '/etc/ssl/certs/rds-global-bundle.pem',
        },
    }
}

# AWS S3 Settings

AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME')
AWS_QUERYSTRING_AUTH = False
AWS_S3_SIGNATURE_NAME = 's3v4'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_S3_VERIFY = True
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

STATIC_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/static/'
MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/media/'

# Backend for file storage
STATICFILES_STORAGE = 'princesscastle.settings.storages.StaticStorage'
DEFAULT_FILE_STORAGE = 'princesscastle.settings.storages.MediaStorage'

# Настройки ImageKit
IMAGEKIT_DEFAULT_FILE_STORAGE = DEFAULT_FILE_STORAGE
IMAGEKIT_CACHE_PREFIX = 'imagekit:'
IMAGEKIT_CACHE_BACKEND_OPTIONS = {
    'storage': DEFAULT_FILE_STORAGE,
    'bucket_name': AWS_STORAGE_BUCKET_NAME,
}

default_storage._wrapped = MediaStorage()

EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST = "smtp.zoho.com"
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SERVER_EMAIL = EMAIL_HOST_USER
EMAIL_ADMIN = EMAIL_HOST_USER

# Конфигурация логирования
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

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
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/app/logs/project.log',
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
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

sentry_sdk.init(
    dsn="https://d97ec34b148074f6168d9c6522cb2af8@o4508247694508032.ingest.us.sentry.io/4508247699161088",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,  # Trace sampling level (1.0 means 100% of all requests)
    send_default_pii=True    # Sending user information to improve diagnostics
)

DOMAIN = config('DOMAIN')
