import json
import logging
from decimal import Decimal

from typing import Any
from django.http import HttpResponse, HttpResponseRedirect

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, CreateView

from cart.cart import Cart
from coupons.models import Coupon
from orders.models import Order
from payment.forms import PaymentConfirmationForm
from payment.models import PaymentConfirmation
from products.models import Product, ProductQuantity, ProductSize, Quantity, Size
from products.turnstile import verify_turnstile
from products.utils import DataMixin

from django.utils.translation import gettext_lazy as _

logger = logging.getLogger('django')


def get_order(request) -> Order:
    """Get order"""
    order_id = request.session.get('order_id')
    order = get_object_or_404(
        Order.objects
        .prefetch_related(
            'items__product__translations',
            'items__product__category__translations',
            'items__product__colors__color__translations'
        ),
        id=order_id
    )

    return order


class PaymentProcessView(LoginRequiredMixin, DataMixin, TemplateView):
    """Handles the payment process."""
    title_page = _('Resumen del pedido')
    template_name = 'payment/process.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add order data to context."""
        context = super().get_context_data(**kwargs)
        order = get_order(self.request)

        return self.get_mixin_context(context, order=order)


class PaymentInstructionsView(LoginRequiredMixin, DataMixin, TemplateView):
    """Handles the payment instructions page."""
    title_page = _('Instrucciónes de pago')
    template_name = 'payment/instructions.html'

    @staticmethod
    def reset_coupon(request, order: Order) -> None:
        """Reset the coupon in the order and session."""
        order.coupon = None
        order.discount = 0
        order.save(update_fields=['coupon', 'discount'])

        request.session.pop('coupon_id', None)
        request.session._cached_coupon = None
        request.session.modified = True

    def validate_coupon(self, request, order: Order) -> HttpResponseRedirect | None:
        """Validate the coupon if exists."""
        coupon_id = request.session.get('coupon_id')
        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id)
                if not coupon.is_valid():
                    messages.warning(request, _("El cupón ya no es válido."))
                    logger.warning(f"El cupón ingresado no es válido: {coupon.code}")

                    self.reset_coupon(request, order)
                    return redirect(reverse('payment:process'))

            except Coupon.DoesNotExist:
                logger.error("Cupón no encontrado en la base de datos.")
        return None

    @staticmethod
    def validate_item_price(item: OrderItem, new_price: float, items_updated: int) -> int:
        """Update a cart item's price if it differs from the current price."""
        if new_price != item.price:
            item.price = new_price
            item.save(update_fields=['price'])
            items_updated += 1

        return items_updated

    def validate_order_items(self, order: Order) -> tuple[int, int]:
        """Validate order items against current product availability and prices."""
        items_updated = 0
        items_removed = 0

        for item in order.items.all():
            try:
                original_product = Product.published.get(pk=item.product.id)
            except Product.DoesNotExist as e:
                logger.warning(f"Articulo no publicado o no existe: {e}")
                item.delete()
                items_removed += 1
                continue

            try:
                # Check price according to product configuration
                if item.quantity:
                    quantity = Quantity.objects.get(quantity=item.quantity)
                    product_quantity = ProductQuantity.objects.get(product=original_product, quantity=quantity)
                    items_updated = self.validate_item_price(item=item,
                                                             new_price=product_quantity.price,
                                                             items_updated=items_updated)

                elif item.size:
                    size = Size.objects.get(translations__size=item.size)
                    product_size = ProductSize.objects.get(product=original_product, size=size)
                    items_updated = self.validate_item_price(item=item,
                                                             new_price=product_size.price,
                                                             items_updated=items_updated)
                else:
                    items_updated = self.validate_item_price(item=item,
                                                             new_price=original_product.price,
                                                             items_updated=items_updated)
            except (Quantity.DoesNotExist, Size.DoesNotExist,
                    ProductQuantity.DoesNotExist, ProductSize.DoesNotExist) as e:
                logger.warning(f"Configuración de producto no disponible: {e}")
                item.delete()
                items_removed += 1
                continue

        return items_updated, items_removed

    def get(self, request, *args: Any, **kwargs: Any) -> HttpResponse | HttpResponseRedirect:
        """Checking the coupon before loading the page"""
        order = get_order(self.request)

        # Validate coupon
        self.validate_coupon(request, order)

        # Validate products
        items_updated, items_removed = self.validate_order_items(order)

        if items_removed > 0:
            messages.warning(request,
                             _("Algunos artículos ya no están disponibles y han sido eliminados de su pedido."))
            return redirect(reverse('payment:process'))

        if items_updated > 0:
            messages.warning(request,
                             _("Los precios de algunos artículos han cambiado y su pedido ha sido actualizado."))
            return redirect(reverse('payment:process'))

        return super().get(request, *args, **kwargs)

    def clear_cart(self, request) -> None:
        """Clears the shopping cart."""
        try:
            cart = Cart(request)
            cart.clear()
        except Exception as e:
            logger.error(f'Carrito de compras no existe: {e}')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Generate context for the template."""
        self.clear_cart(self.request)

        order = get_order(self.request)

        # Remove order_id from session after receiving order
        self.request.session.pop('order_id', None)
        self.request.session.modified = True

        order.send_payment_instructions_email()

        context = super().get_context_data(**kwargs)
        context = self.get_mixin_context(context, order=order,
                                         card=settings.CARD_FOR_PAYMENTS,
                                         name=settings.NAME_FOR_PAYMENTS,
                                         bank=settings.BANK_FOR_PAYMENTS)
        return context


class PaymentConfirmationView(LoginRequiredMixin, CreateView):
    """View for creating Payment Confirmation."""
    model = PaymentConfirmation
    form_class = PaymentConfirmationForm
    template_name = 'payment/confirmation.html'
    success_url = reverse_lazy('payment:completed')

    def form_valid(self, form: PaymentConfirmationForm) -> HttpResponse:
        """Checking Turnstile and assign the logged-in user to the suggestion before saving."""
        token = form.cleaned_data.get('cf_turnstile_response')
        if not verify_turnstile(token, self.request.META.get('REMOTE_ADDR')):
            form.add_error(None, _('La validación del captcha falló'))
            return self.form_invalid(form)

        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add extra context including Title and Turnstile."""
        context = super().get_context_data(**kwargs)
        context['title'] = _("Confirmación de pago")
        context['CLOUDFLARE_TURNSTILE_SITE_KEY'] = settings.CLOUDFLARE_TURNSTILE_SITE_KEY
        return context


class PaymentCompletedView(DataMixin, TemplateView):
    """Displays a confirmation page after successful payment."""
    template_name = 'payment/completed.html'
    title_page = _('Pago exitoso!')


class PaymentCanceledView(DataMixin, TemplateView):
    """Displays a cancellation page if the payment process was interrupted."""
    template_name = 'payment/canceled.html'
    title_page = _('Hubo un problema al procesar su pago.')


@method_decorator(csrf_exempt, name='dispatch')
class UpdatePartialPaymentStatusView(LoginRequiredMixin, View):
    """Updates the status of partial payment for an order via AJAX."""

    def post(self, request, *args: Any, **kwargs: Any) -> JsonResponse:
        try:
            data = json.loads(request.body)
            order_id = request.session.get('order_id')
            partial_payment = data.get('partial_payment') == 'true'

            # Update partial_payment status in the order
            order = Order.objects.get(id=order_id)
            order.partial_payment = partial_payment
            order.save()

            total_cost = order.get_total_cost()
            partial_payment_cost = order.get_total_cost_with_partial_payment() if partial_payment else total_cost

            return JsonResponse({
                'status': 'ok',
                'partial_payment': partial_payment,
                'total_cost': total_cost,
                'partial_payment_cost': partial_payment_cost
            })
        except Order.DoesNotExist:
            logger.error('Error al obtener un pedido para UpdatePartialPaymentStatusView')
            return JsonResponse({'status': 'error', 'message': 'Order not found'})
        except Exception as e:
            logger.error(f'Error al actualizar pago parcial: {e}')
            return JsonResponse({'status': 'error', 'message': str(e)})
