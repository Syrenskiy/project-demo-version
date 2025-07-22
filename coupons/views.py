from django.contrib import messages
from django.utils import timezone

from django.shortcuts import redirect
from django.views import View

from cart.cart import Cart
from coupons.forms import CouponApplyForm
from coupons.models import Coupon

from django.utils.translation import gettext_lazy as _


class CouponApplyView(View):
    """
    View to handle coupon application in the cart. Validates and applies the coupon code,
    updating the session with the coupon details if the coupon is valid and has remaining uses.
    """
    def post(self, request):
        """
        Handles POST request to apply a coupon to the cart. Validates the coupon code
        against active coupons within the valid date range, and stores the coupon in
        the session if valid and not exhausted.
        """
        now = timezone.now()
        form = CouponApplyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            cart = Cart(request)
            try:
                # Retrieve an active, valid coupon
                coupon = Coupon.objects.get(code__iexact=code, valid_from__lte=now,
                                            valid_to__gte=now, active=True)
                # Try using the coupon
                if not coupon.use():
                    messages.error(request, _('Este cupón ha alcanzado su límite de uso.'))
                    return redirect('cart:cart_detail')

                # Apply the coupon to the session
                request.session['coupon_id'] = coupon.id
                messages.success(request, _('El cupón se aplicó correctamente!'))
            except Coupon.DoesNotExist:
                request.session['coupon_id'] = None
                messages.error(request, _('Este cupón no existe o no es válido.'))

            # Clear cached coupon if it exists to ensure the new coupon is applied
            if hasattr(cart, '_cached_coupon'):
                delattr(cart, '_cached_coupon')

        return redirect('cart:cart_detail')
