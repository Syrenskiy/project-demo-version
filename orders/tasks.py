from celery import shared_task
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import translation

from orders.models import Order
from django.conf import settings

from django.utils.translation import gettext_lazy as _


class OrderEmailSender:
    """
    Class responsible for building and sending order-related emails.
    Includes methods to build the email context and message details.
    """
    def __init__(self, order):
        self.order = order
        self.message, self.context = self.build_message_context()

    def build_message_context(self) -> tuple[str, dict[str, Any]]:
        """
        Build the email message and context details based on order data.
        Returns the email message string and context dictionary.
        """
        order_created_date = self.order.created.strftime("%d.%m.%Y %H:%M")
        message = ''
        for item in self.order.items.all():
            quantity = (_('\tPiezas: %(quantity)s\n') % {'quantity': item.quantity}) if item.quantity else ''
            size = (_('\tTalla: %(size)s\n') % {'size': item.size}) if item.size else ''
            message += (
                    _('\tArtículo: %(product_name)s\n') % {'product_name': item.product.name} +
                    _('\tColor: %(color)s\n') % {'color': item.color} +
                    f'{size}{quantity}' +
                    _('\tPrecio por unidad: $%(price)s\n') % {'price': item.price} +
                    _('\tCantidad: %(product_quantity)s\n') % {'product_quantity': item.product_quantity} +
                    _('\tTotal: $%(total_cost)s\n\n') % {'total_cost': item.get_cost()}
            )

        subtotal = f'${self.order.get_total_cost_before_discount():.2f}'
        message += _('\nSubTotal: %(subtotal)s\n\n') % {'subtotal': subtotal}

        discount = ''
        if self.order.coupon:
            discount = f'${self.order.get_discount():.2f}'
            message += _('\nDescuento: %(discount)s\n') % {'discount': discount}

        delivery_cost = f'${self.order.delivery.cost:.2f}'
        total = f'${self.order.get_total_cost():.2f}'

        message += (
                _('\nCosto de entrega: %(delivery_cost)s\n\n') % {'delivery_cost': delivery_cost} +
                _('\nTotal: %(total)s\n\n') % {'total': total}
        )

        partial_payment = ''
        if self.order.partial_payment:
            partial_payment = f'${self.order.get_total_cost_with_partial_payment():.2f}'
            message += _('\nPago parcial: %(partial_payment)s\n') % {'partial_payment': partial_payment}

        context = {
            'order': self.order,
            'order_created_date': order_created_date,
            'subtotal': subtotal,
            'discount': discount,
            'delivery_cost': delivery_cost,
            'total': total,
            'partial_payment': partial_payment
        }

        return message, context

    def send(self, subject: str, message: str, to_email: str | list[str],
             template_name: str, message_continuation: bool = True) -> int:
        """Send an email, optionally rendering an HTML template."""
        if message_continuation:
            message += self.message
        html_message = render_to_string(template_name, self.context)
        return send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            to_email if isinstance(to_email, list) else [to_email],
            html_message=html_message,
        )


@shared_task
def send_order_confirmation_to_client(order_id: int) -> None:
    """
    Task to send order confirmation email to the client.
    Activates translation for the client's language and constructs the email content.
    """
    order = Order.objects.get(id=order_id)
    translation.activate(order.language)
    email_sender = OrderEmailSender(order)
    subject = _('Su Orden de Princess Castle')
    template_name = 'orders/emails/order_confirmation_to_client.html'
    message = (
            _('\nQuerido(a) %(first_name)s,\n\n') % {'first_name': order.first_name} +
            _('Has realizado(a) pedido con éxito.\n\n') +
            _('Numero del pedido: %(order_id)s\n') % {'order_id': order_id} +
            _('Recibida: %(order_created_date)s\n\n') % {
                'order_created_date': email_sender.context['order_created_date']} +
            _('Dirección de la entrega: %(order_delivery)s\n') % {
                'order_delivery': order.address if order.delivery.cost else order.delivery.place} +
            _('Productos:\n')
    )

    email_sender.send(subject, message, order.email, template_name)

    return translation.deactivate()


@shared_task
def send_order_confirmation_to_seller(order_id: int) -> int:
    """
    Task to notify the seller of a new order.
    Constructs and sends an email with order and customer details.
    """
    order = Order.objects.get(id=order_id)
    email_sender = OrderEmailSender(order)
    subject = 'Nuevo Pedido de Princess Castle'
    template_name = 'orders/emails/order_confirmation_to_seller.html'
    order_updated_date = order.updated.strftime("%d.%m.%Y %H:%M")
    email_sender.context['order_updated_date'] = order_updated_date
    message = (
        f'Numero del pedido: {order_id}\n'
        f'Recibida: {email_sender.context['order_created_date']}\n'
        f'Pagada: {order_updated_date}\n\n'
        f'Información del cliente:\n'
        f'\tNombre: {order.first_name}\n'
        f'\tApellido: {order.last_name}\n'
        f'\tCorreo electrónico: {order.email}\n'
        f'\tTeléfono: {order.phone}\n'
        f'\tDirección de la entrega: {order.address if order.delivery.cost else order.delivery.place}\n'
        f'\tEstado: {'Pagado' if order.paid_full else 'Pagado Parcialmente'}\n\n'
        f'Productos:\n'
    )

    return email_sender.send(subject, message, settings.SELLERS_EMAILS, template_name)


@shared_task
def send_comment_invitation_to_client(order_id: int) -> None:
    """
    Task to invite the client to leave feedback on purchased products.
    Constructs a message with a link to the review page and sends it to the client.
    """
    order = Order.objects.get(id=order_id)
    translation.activate(order.language)
    email_sender = OrderEmailSender(order)
    subject = _('Gracias por su compra en Princess Castle!')
    template_name = 'orders/emails/comment_invitation.html'
    relative_url = reverse('users:comments')
    review_link = f"{settings.DOMAIN}{relative_url}"
    email_sender.context['review_link'] = review_link
    message = (
            _('\nQuerido(a) %(first_name)s,\n\n') % {'first_name': order.first_name} +
            _('\nNos alegra que haya completado su pedido número %(order_id)s.\n') % {'order_id': order.id} +
            _('\nEsperamos que disfrute de su compra.\n\n') +
            _('\nSi tiene unos minutos, le invitamos a dejar su opinión sobre los productos adquiridos: %('
              'review_link)s\n\n') % {'review_link': review_link} +
            _('\nGracias por confiar en Princess Castle.\n')
    )

    email_sender.send(subject, message, order.email, template_name, message_continuation=False)

    return translation.deactivate()


@shared_task
def send_payment_instructions(order_id: int) -> None:
    """Task to send payment instructions to the client for a specific order."""
    order = Order.objects.get(id=order_id)
    translation.activate(order.language)
    email_sender = OrderEmailSender(order)
    subject = _('Princess Castle')
    template_name = 'payment/emails/payment_instructions.html'

    if order.partial_payment:
        total = f'${order.get_total_cost_with_partial_payment():.2f}'
        partial = _('Usted eligió pago parcial, el resto se pagará en la entrega.\n')
    else:
        total = f'${order.get_total_cost():.2f}'
        partial = ''

    card = settings.CARD_FOR_PAYMENTS
    name = settings.NAME_FOR_PAYMENTS
    bank = settings.BANK_FOR_PAYMENTS
    # payment_confirmation_link = _('%(domain)s/es/pago/confirmacion-pago/') % {'domain': settings.DOMAIN}
    payment_confirmation_link = redirect(reverse('payment:process'))
    email_sender.context['payment_confirmation_link'] = payment_confirmation_link
    email_sender.context['card'] = card
    email_sender.context['name'] = name
    email_sender.context['bank'] = bank

    message = (
            _('\nInstrucciones de Pago.\n\n') +
            _('\n\nQuerido(a) %(first_name)s,\n\n') % {'first_name': order.first_name} +
            _('Complete su pago siguiendo las instrucciones a continuación.\n\n') +
            _('Número de pedido: %(order_id)s\n') % {'order_id': order_id} +
            _('Total a pagar: %(total)s\n') % {'total': total} +
            partial +
            _('\nMétodos de Pago\n\n') +
            _('Pago por transferencia bancaria\n') +
            _('Pago en efectivo en OXXO o tiendas de conveniencia\n\n') +
            _('Número de tarjeta: %(card)s\n') % {'card': card} +
            _('Nombre del titular: %(name)s\n') % {'name': name} +
            _('Banco: %(bank)s\n\n') % {'bank': bank} +
            _('Su pedido comenzará a procesarse una vez que recibamos la confirmación del pago.\n') +
            _('Después de realizar el pago, cargue una foto del comprobante o captura de pantalla de la '
              'transferencia.\n') +
            '%(payment_confirmation_link)s\n' % {'payment_confirmation_link': payment_confirmation_link}
    )

    email_sender.send(subject, message, order.email, template_name, message_continuation=False)

    return translation.deactivate()
