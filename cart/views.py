import logging

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView

from django.http import HttpResponseRedirect

from cart.cart import Cart
from coupons.forms import CouponApplyForm
from products.forms import CartAddProductForm
from products.models import Product, Color
from products.utils import DataMixin

from django.utils.translation import gettext_lazy as _


logger = logging.getLogger('django')


class BaseCartView(View):
    """
    Base view for handling cart modifications such as adding, subtracting,
    or removing items. Utilizes `modify_cart` method to handle cart actions.
    """
    def modify_cart(self, request, product_id: int, color_slug: str, action: str) -> HttpResponseRedirect:
        """Modifies the cart based on the specified action ('add', 'subtract', 'remove')."""
        try:
            cart = Cart(self.request)
            product = get_object_or_404(Product, id=product_id)
            color = get_object_or_404(Color, translations__slug=color_slug)

            form = CartAddProductForm(request.POST, product=product, color=color)

            if form.is_valid():
                cd = form.cleaned_data
                size = cd['size']
                quantity = cd['quantity']
                product_quantity = cd.get('product_quantity')
                price = cd.get('price')

                # Apply the specified cart modification action
                if action == "add":
                    cart.add(product=product, color=color, price=price,
                             product_quantity=product_quantity, size=size, quantity=quantity)
                elif action == "subtract":
                    cart.subtract(product=product, color=color, size=size, quantity=quantity)
                elif action == "remove":
                    cart.remove(product=product, color=color, size=size, quantity=quantity)

                return redirect('cart:cart_detail')

            else:
                if action == "add":
                    required_fields = {
                        'size': _('Elija la talla.'),
                        'quantity': _('Elija el número de piezas.'),
                        'product_quantity': _('Elija la cantidad.')
                    }
                    for field, error_message in required_fields.items():
                        if field not in form.cleaned_data:
                            messages.error(request, error_message)

                storage = messages.get_messages(request)
                storage.used = False

                return redirect('product', category_slug=product.category.slug, product_slug=product.slug,
                                color_slug=color.slug)
        except Exception as e:
            logger.error(f"Error al modificar carrito: {e}")
            return redirect('cart:cart_detail')


class CartAddView(BaseCartView):
    """Handles the addition of items to the cart through a POST request."""
    def post(self, request, product_id: int, color_slug: str) -> HttpResponseRedirect:
        return self.modify_cart(request, product_id, color_slug, action="add")


class CartSubtractView(BaseCartView):
    """Handles the subtraction of items from the cart through a POST request."""
    def post(self, request, product_id: int, color_slug: str) -> HttpResponseRedirect:
        return self.modify_cart(request, product_id, color_slug, action="subtract")


class CartRemoveView(BaseCartView):
    """Handles the removal of items from the cart through a POST request."""
    def post(self, request, product_id: int, color_slug: str) -> HttpResponseRedirect:
        return self.modify_cart(request, product_id, color_slug, action="remove")


class CartDetailView(DataMixin, TemplateView):
    """Displays the cart details, including items, quantities, and any applied coupons."""
    template_name = 'cart/detail.html'
    title_page = _('Su Carrito Princess Castle')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Adds cart items and coupon application form to the context."""
        context = super().get_context_data(**kwargs)
        cart = Cart(self.request)

        cart_items = []
        for item in cart:
            item['update_product_quantity_form'] = CartAddProductForm(
                initial={
                    'product_quantity': item['product_quantity'],
                    'size': item['size'],
                    'quantity': item['quantity'],
                    'override': True
                }
            )
            item['color_slug'] = item['color'].slug
            cart_items.append(item)

        context['cart'] = cart
        context['cart_items'] = cart_items
        context['coupon_apply_form'] = CouponApplyForm()
        return context
