from django import forms
from django.core.exceptions import ValidationError

from orders.models import Order, Delivery

from django.utils.translation import gettext_lazy as _


class OrderCreateForm(forms.ModelForm):
    """
    Form for creating an order, capturing the essential fields required for order creation.
    Populates fields with user data if provided.
    """
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'phone', 'delivery', 'address']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control bg-light-gray',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control bg-light-gray',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control bg-light-gray',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control bg-light-gray',
            }),
            'delivery': forms.Select(attrs={
                'class': 'form-select bg-light-gray',
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control bg-light-gray',
            }),
        }

    def __init__(self, *args, **kwargs):
        # Retrieve the user from kwargs if provided
        user = kwargs.pop('user', None)
        super(OrderCreateForm, self).__init__(*args, **kwargs)

        # Sorting delivery options by order_field
        self.fields['delivery'].queryset = (Delivery.objects
                                            .prefetch_related('translations').order_by('order_field'))

        # Ensure specific fields are required
        required_fields = ['first_name', 'last_name', 'email', 'phone']
        for field_name in required_fields:
            self.fields[field_name].required = True

        # Autofill user details if user instance is passed
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            self.fields['phone'].initial = user.phone
            self.fields['address'].initial = user.address

        # Address field is optional
        self.fields['address'].required = False

        self.fields['delivery'].empty_label = _("Seleccione una opción")

    def clean_address(self):
        """
        Validate the address field based on delivery option.
        Raises a ValidationError if 'Home Delivery' is chosen but address is not provided.
        """
        delivery = self.cleaned_data.get('delivery')
        if not delivery:
            raise ValidationError(_('Seleccione una opción de entrega'))

        address = self.cleaned_data.get('address')
        address_translation = ('A Domicilio', 'Home Delivery', 'Доставка на Дом')
        if delivery.place in address_translation and not address:
            self.add_error('address', ValidationError(_('Ingrese su dirección')))
        return address

    def clean_phone(self):
        """Validate the phone field."""
        phone = self.cleaned_data.get('phone')

        if not phone or len(phone) < 10:
            self.add_error('phone', ValidationError(_('Número telefónico debe contener mínimo 10 dígitos')))
        return phone

