import logging

from PIL import Image
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordResetForm, SetPasswordForm, \
    PasswordChangeForm

from django import forms
from django.forms import ClearableFileInput

from django.utils.translation import gettext_lazy as _


logger = logging.getLogger('django')


class CustomClearableFileInput(ClearableFileInput):
    template_name = 'users/widgets/custom_clearable_file_input.html'


class LoginUserForm(AuthenticationForm):
    """Form for user login, extending Django's AuthenticationForm."""
    username = forms.CharField(
        label=_("Nombre de usuario o Correo electrónico"),
        widget=forms.TextInput(attrs={'class': 'form-control bg-light-gray'})
    )
    password = forms.CharField(
        label=_("Contraseña"),
        widget=forms.PasswordInput(attrs={'class': 'form-control bg-light-gray'})
    )
    cf_turnstile_response = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = get_user_model()


class RegisterUserForm(UserCreationForm):
    """Form for new user registration with required email field."""
    email = forms.EmailField(required=True,
                             label=_('Correo electrónico'),
                             widget=forms.EmailInput(attrs={'class': 'form-control bg-light-gray'}))

    password1 = forms.CharField(
        label=_("Contraseña"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", 'class': 'form-control bg-light-gray'}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=_("Confirmación de contraseña"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", 'class': 'form-control bg-light-gray'}),
        strip=False,
        help_text=_("Ingrese la misma contraseña que antes, para verificación."),
    )
    cf_turnstile_response = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control bg-light-gray'}),
        }

    def clean_email(self):
        """Validate that the provided email is unique."""
        email = self.cleaned_data['email']
        if get_user_model().objects.filter(email=email).exists():
            raise forms.ValidationError(_("Este correo electrónico ya existe"))
        return email


class PasswordResetUserForm(PasswordResetForm):
    email = forms.EmailField(
        label=_("Correo electrónico"),
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email", 'class': 'form-control bg-light-gray'}),
    )

    class Meta:
        model = get_user_model()


class SetPasswordUserForm(SetPasswordForm):
    """
    A form that lets a user set their password without entering the old
    password
    """
    new_password1 = forms.CharField(
        label=_("Nueva contraseña"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", 'class': 'form-control bg-light-gray'}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_("Confirmación de nueva contraseña"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", 'class': 'form-control bg-light-gray'}),
    )

    class Meta:
        model = get_user_model()


class PasswordChangeUserForm(SetPasswordUserForm, PasswordChangeForm):
    """Form for password change, extending Django's PasswordChangeForm."""
    old_password = forms.CharField(
        label=_("Contraseña anterior"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password", "autofocus": True, 'class': 'form-control bg-light-gray'}
        ),
    )

    class Meta:
        model = get_user_model()


class ProfileUserForm(forms.ModelForm):
    """Form for updating user profile with fields for personal and contact information."""

    username = forms.CharField(
        disabled=True,
        label=_('Usuario'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': True})
    )
    email = forms.EmailField(
        disabled=True,
        required=False,
        label=_('Correo electrónico'),
        widget=forms.EmailInput(attrs={'class': 'form-control', 'readonly': True})
    )
    date_birth = forms.DateField(
        label=_("Fecha de nacimiento"),
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control bg-light-gray',
            'type': 'date',
        })
    )

    class Meta:
        model = get_user_model()
        fields = ['photo', 'username', 'first_name', 'last_name', 'email', 'date_birth', 'phone', 'address']
        widgets = {
            'photo': CustomClearableFileInput(attrs={'class': 'form-control bg-light-gray'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control bg-light-gray'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control bg-light-gray'}),
            'phone': forms.TextInput(attrs={'class': 'form-control bg-light-gray'}),
            'address': forms.TextInput(attrs={'class': 'form-control bg-light-gray'}),
        }

    def clean_photo(self):
        """Validar que la foto subida sea válida."""
        image = self.cleaned_data.get('photo')
        if image:
            allowed_formats = ['jpeg', 'png', 'gif', 'webp', 'bmp', 'tiff']
            max_size_mb = 5  # Максимальный размер для аватара

            logger.info(f"Inicio de validación de la foto del perfil: {image.name}")

            # Validar contenido de la imagen usando Pillow
            try:
                img = Image.open(image)
                logger.info(f"Formato detectado de la foto: {img.format.lower()}")
                if img.format.lower() not in allowed_formats:
                    logger.warning(f"Formato no permitido para la foto: {img.format.lower()}")
                    raise forms.ValidationError(_("El archivo seleccionado no tiene un formato válido."))
            except Exception as e:
                logger.error(f"Error al validar la foto {image.name}: {str(e)}")
                raise forms.ValidationError(_("El archivo seleccionado no es una imagen válida."))

            # Validar tamaño del archivo
            if image.size > max_size_mb * 1024 * 1024:
                logger.warning(f"El tamaño de la foto excede el límite permitido: {image.size / (1024 * 1024):.2f} MB")
                raise forms.ValidationError(
                    _("El archivo seleccionado supera el tamaño máximo permitido de 5 MB.")
                )

            logger.info(f"La foto {image.name} pasó la validación correctamente.")

        return image
