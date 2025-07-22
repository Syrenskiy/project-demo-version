from django import forms

from django.utils.translation import gettext_lazy as _


class CouponApplyForm(forms.Form):
    code = forms.CharField(label=_('Cupón'), widget=forms.TextInput(
        attrs={
            'class': 'form-control bg-light-gray',
            'placeholder': _('Ingresar Cupón'),
        }
    ))
