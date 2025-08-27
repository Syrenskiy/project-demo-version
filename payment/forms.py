import logging

from PIL import Image
from django import forms
from django.core.files.uploadedfile import UploadedFile

from django.utils.translation import gettext_lazy as _
from turnstile.fields import TurnstileField

from payment.models import PaymentConfirmation
from users.forms import CustomClearableFileInput

logger = logging.getLogger('django')


class PaymentConfirmationForm(forms.ModelForm):
    image = forms.ImageField(label=_('Comprobante de pago'), widget=CustomClearableFileInput(attrs={'class': 'form-control bg-light-gray'}))
    cf_turnstile_response = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = PaymentConfirmation
        fields = ['order_id', 'image']
        widgets = {
            'order_id': forms.TextInput(attrs={'class': 'form-control bg-light-gray'}),
        }

    def clean_image(self) -> UploadedFile:
        """Validate that the image is of an allowed type and has a valid size."""
        image = self.cleaned_data.get('image')
        allowed_formats = ['jpeg', 'png', 'gif', 'webp', 'bmp', 'tiff']
        max_size_mb = 20

        logger.info(f"Inicio de validación de la imagen")

        # Check image content using Pillow
        try:
            img = Image.open(image)
            logger.info(f"Formato detectado de la imagen: {img.format.lower()}")
            if img.format.lower() not in allowed_formats:
                logger.warning(f"Formato no permitido para la imagen: {img.format.lower()}")
                raise forms.ValidationError(_("El archivo seleccionado no tiene un formato válido."))
        except Exception as e:
            logger.error(f"Error al validar la imagen {image.name}: {str(e)}")
            raise forms.ValidationError(_("El archivo seleccionado no es una imagen válida."))

        # Check file size
        if image.size > max_size_mb * 1024 * 1024:
            logger.warning(
                f"El tamaño de la imagen excede el límite permitido: {image.size / (1024 * 1024):.2f} MB")
            raise forms.ValidationError(
                _("El archivo seleccionado supera el tamaño máximo permitido de 20 MB.")
            )
        logger.info(f"La imagen {image.name} pasó la validación correctamente.")

        return image
