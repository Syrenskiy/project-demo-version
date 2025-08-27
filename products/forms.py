import logging

from PIL import Image
from django import forms
from django.core.exceptions import ValidationError
from turnstile.fields import TurnstileField

from django.core.files.uploadedfile import UploadedFile

from products.models import Product, Quantity, Size, Comment, ProductSuggestion, ProductSuggestionImage

from django.utils.translation import gettext_lazy as _

from users.forms import CustomClearableFileInput

logger = logging.getLogger('django')

# Options for product quantity selection (1-10)
PRODUCT_QUANTITY_CHOICES = [(i, str(i)) for i in range(1, 11)]


class CartAddProductForm(forms.ModelForm):
    """Form for adding a product to the shopping cart, including color, size, and quantity options."""
    product_quantity = forms.TypedChoiceField(choices=PRODUCT_QUANTITY_CHOICES, coerce=int, label=_('Cantidad'))
    color = forms.CharField(required=True, widget=forms.HiddenInput, label=_('Color'))
    price = forms.DecimalField(required=True, max_digits=10, decimal_places=2,
                               widget=forms.HiddenInput, label=_('Precio'))
    override = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)

    size = forms.ModelChoiceField(
        queryset=Size.objects.none(),
        widget=forms.RadioSelect(attrs={'class': 'custom-radio'}),
        required=False,
        label=_('Talla'),
        error_messages={'required': _('Por favor, seleccione la talla.')}
    )
    quantity = forms.ModelChoiceField(
        queryset=Quantity.objects.none(),
        widget=forms.RadioSelect(attrs={'class': 'custom-radio'}),
        required=False,
        label=_('Piezas'),
        error_messages={'required': _('Por favor, seleccione la cantidad de piezas.')}
    )

    class Meta:
        model = Product
        fields = ['color', 'size', 'quantity', 'product_quantity', 'price', 'override']

    def __init__(self, *args, **kwargs):
        """Initialize the form with specific product context and populate choices for size and quantity."""
        product = kwargs.pop('product', None)
        color = kwargs.pop('color', None)
        super().__init__(*args, **kwargs)

        if product:
            # Set available sizes and quantities based on the product
            if product.size.exists():
                self.fields['size'].queryset = product.size.all()
                self.fields['size'].required = True
            else:
                self.fields['size'].widget = forms.HiddenInput()

            if product.quantity.exists():
                self.fields['quantity'].queryset = product.quantity.all()
                self.fields['quantity'].required = True
            else:
                self.fields['quantity'].widget = forms.HiddenInput()

            self.fields['color'].initial = color.name
            self.fields['price'].initial = product.price if product.price else 0


class CommentForm(forms.ModelForm):
    """Form for submitting product comments, capturing rating and text."""
    class Meta:
        model = Comment
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.HiddenInput(),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class SearchForm(forms.Form):
    """Form for searching products by a query string."""
    query = forms.CharField(
        label=_("Búsqueda"),
        widget=forms.TextInput(attrs={'class': 'form-control bg-light-gray', 'placeholder': _('Buscar productos...')})
    )


class ProductSuggestionForm(forms.ModelForm):
    """Form for user suggestions."""
    image_1 = forms.ImageField(required=False, label=_('Imagen 1'),
                               widget=CustomClearableFileInput(attrs={'class': 'form-control bg-light-gray'}))
    image_2 = forms.ImageField(required=False, label=_('Imagen 2'),
                               widget=CustomClearableFileInput(attrs={'class': 'form-control bg-light-gray'}))
    image_3 = forms.ImageField(required=False, label=_('Imagen 3'),
                               widget=CustomClearableFileInput(attrs={'class': 'form-control bg-light-gray'}))
    cf_turnstile_response = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = ProductSuggestion
        fields = ['description', 'image_1', 'image_2', 'image_3', 'phone']
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control bg-light-gray',
                'rows': 4,
                'placeholder': _('Escribe tu propuesta aquí...')
            }),
            'phone': forms.TextInput(attrs={'class': 'form-control bg-light-gray'}),
        }

    def __init__(self, *args, **kwargs):
        # Retrieve the user from kwargs if provided
        user = kwargs.pop('user', None)
        super(ProductSuggestionForm, self).__init__(*args, **kwargs)

        if user:
            self.fields['phone'].initial = user.phone

    def clean_single_image(self, image: UploadedFile | None) -> UploadedFile | None:
        """Validate that the image is of an allowed type and has a valid size."""
        if image:
            allowed_formats = ['jpeg', 'png', 'gif', 'webp', 'bmp', 'tiff']
            max_size_mb = 10

            logger.info(f"Inicio de validación de la imagen: {image.name}")

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
                    _("El archivo seleccionado supera el tamaño máximo permitido de 10 MB.")
                )
            logger.info(f"La imagen {image.name} pasó la validación correctamente.")

        return image

    def clean_image_1(self) -> UploadedFile | None:
        """Validate that only valid images are uploaded for image_1."""
        return self.clean_single_image(self.cleaned_data.get('image_1'))

    def clean_image_2(self) -> UploadedFile | None:
        """Validate that only valid images are uploaded for image_2."""
        return self.clean_single_image(self.cleaned_data.get('image_2'))

    def clean_image_3(self) -> UploadedFile | None:
        """Validate that only valid images are uploaded for image_3."""
        return self.clean_single_image(self.cleaned_data.get('image_3'))

    def save(self, commit: bool = True) -> ProductSuggestion:
        """Save the suggestion and associated images."""
        suggestion = super().save(commit=commit)
        if commit:  # Save images only if suggestion is already saved
            for image_field in ['image_1', 'image_2', 'image_3']:
                image = self.cleaned_data.get(image_field)
                if image:
                    ProductSuggestionImage.objects.create(suggestion=suggestion, image=image)
                    logger.info(f"La imagen {image.name} fue guardada correctamente para la sugerencia ID {suggestion.id}")
        return suggestion
