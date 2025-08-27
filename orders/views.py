import logging

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required

from typing import Any
from decimal import Decimal
from django.http import HttpResponse, JsonResponse

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView

from cart.cart import Cart
from orders.forms import OrderCreateForm
from orders.models import OrderItem, Order, Delivery
from products.models import Product, ProductQuantity, ProductSize
from products.utils import DataMixin

from django.utils.translation import gettext_lazy as _

logger = logging.getLogger('django')


class OrderCreateView(LoginRequiredMixin, DataMixin, FormView):
    """
    View for creating an order, handling form submission and validation.
    Renders the order creation template and processes the order on successful form submission.
    """
    form_class = OrderCreateForm
    template_name = 'orders/order/create.html'
    success_url = reverse_lazy('payment:process')
    title_page = _('Su Pedido')

    def get_form_kwargs(self) -> dict[str, Any]:
        """Pass the user instance to the form for autofill purposes."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form: OrderCreateForm) -> HttpResponse:
        """Save the order and its items on valid form submission, then redirect to payment processing."""
        cart = Cart(self.request)
        order = form.save(commit=False)

        order.user = self.request.user
        order.delivery = form.cleaned_data['delivery']
        order.language = self.request.LANGUAGE_CODE

        order = self.process_cart_coupon(form, cart, order)
        if order is None:
            return self.render_to_response(self.get_context_data(form=form))

        items_updated = self.process_cart_items(cart)
        if items_updated > 0:
            messages.warning(self.request, _("Algunos artículos han sido actualizados. Por favor confirme su pedido."))
            return self.render_to_response(self.get_context_data(form=form))

        order.save()

        self.create_order_items(cart, order)

        # Store the order ID in session
        self.request.session['order_id'] = order.id
        return super().form_valid(form)

    def process_cart_coupon(self, form: OrderCreateForm, cart: Cart, order: Order) -> Order | None:
        """Process any coupon in the cart and apply it to the order if valid."""
        if cart.coupon:
            if cart.coupon.is_valid():
                order.coupon = cart.coupon
                order.discount = cart.coupon.discount
            else:
                messages.warning(self.request, _("El cupón ya no es válido."))
                logger.warning(f"El cupón ingresado no es valido: {cart.coupon.code}")
                cart.coupon = None
                return None

        return order

    def process_cart_items(self, cart: Cart) -> int:
        """Validate and update prices for all items in the cart if needed."""
        items_updated = 0

        for item in cart:
            try:
                original_product = Product.published.get(pk=item['product'].id)
            except Product.DoesNotExist as e:
                logger.warning(f"Articulo no publicado o no existe: {e}")
                cart.remove(item['product'], item['color'], item['size'], item['quantity'])
                items_updated += 1
                continue

            if item['quantity']:
                product_quantity = ProductQuantity.objects.get(product=original_product, quantity=item['quantity'])
                items_updated = self.update_item_price(cart=cart,
                                                       item=item,
                                                       new_price=product_quantity.price,
                                                       items_updated=items_updated)

            elif item['size']:
                product_size = ProductSize.objects.get(product=original_product, size=item['size'])
                items_updated = self.update_item_price(cart=cart,
                                                       item=item,
                                                       new_price=product_size.price,
                                                       items_updated=items_updated)
            else:
                items_updated = self.update_item_price(cart=cart,
                                                       item=item,
                                                       new_price=original_product.price,
                                                       items_updated=items_updated)

        return items_updated

    @staticmethod
    def update_item_price(cart: Cart, item: dict, new_price: Decimal, items_updated: int) -> int:
        """Update a cart item's price if it differs from the current price."""
        if new_price != item['price']:
            item['price'] = new_price
            cart.update(item['product'], item['color'], item['price'], item['size'], item['quantity'])
            items_updated += 1

        return items_updated

    @staticmethod
    def create_order_items(cart: Cart, order: Order) -> Order:
        """Create OrderItem for each item in the cart."""
        for item in cart:
            try:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    color=item['color'],
                    size=item['size'],
                    quantity=item['quantity'],
                    price=item['price'],
                    product_quantity=item['product_quantity']
                )
            except Exception as e:
                logger.error(f"Error al crear articulo para nueva orden: {e}")

        return order

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add the shopping cart object to the context for template rendering."""
        context = super().get_context_data(**kwargs)
        context['cart'] = Cart(self.request)
        return context


class GetDeliveryCostView(View):
    """
    View to fetch and return the delivery cost for a given delivery option.
    Responds with a JSON object containing the cost or an error if the delivery option is not found.
    """

    def get(self, request, delivery_id: int, *args: Any, **kwargs: Any) -> JsonResponse:
        try:
            delivery = Delivery.objects.get(id=delivery_id)
            return JsonResponse({'delivery_cost': float(delivery.cost)})
        except Delivery.DoesNotExist:
            logger.error(f'Error al obtener la entrega, lugar no encontrado con id: {delivery_id}')
            return JsonResponse({'error': 'Delivery not found'}, status=404)


@staff_member_required
def admin_order_detail(request, order_id: int) -> HttpResponse:
    """
    View to display the details of an order for admin users.
    Renders the order detail template with order information.
    """
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'admin/orders/order/detail.html', {'order': order})
