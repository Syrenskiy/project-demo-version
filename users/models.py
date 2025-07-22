from django.contrib.auth.models import AbstractUser
from django.db import models

from django.utils.translation import gettext_lazy as _
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, Transpose


class User(AbstractUser):
    """Custom user model with additional fields for profile photo, phone, address, and birth date."""

    photo = models.ImageField(upload_to="users/%Y/%m/%d/", blank=True, null=True,
                              verbose_name=_("Foto de perfil"))
    photo_profile = ImageSpecField(source='photo', processors=[Transpose(), ResizeToFill(400, 400)],
                                   format='JPEG', options={'quality': 70})
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Teléfono'))
    address = models.CharField(max_length=150, blank=True, null=True, verbose_name=_('Dirección'))
    date_birth = models.DateField(blank=True, null=True, verbose_name=_("Fecha de nacimiento"))
