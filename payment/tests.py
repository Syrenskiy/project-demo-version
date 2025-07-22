import json
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from unittest.mock import patch, MagicMock
from orders.models import Order, OrderItem, Delivery
from coupons.models import Coupon
from products.models import Product, Category, Color, Size, Quantity, ProductColor
from users.models import User


User = get_user_model()


# class MockStripeSession:
#     """Mock class to simulate a Stripe checkout session in tests."""
#     def __init__(self, id, url):
#         self.id = id
#         self.url = url
#
#
# class PaymentTests(TestCase):
#     """Test cases for payment processing views and Stripe integration."""
#     def setUp(self):
#         """Setup test data including user, product, coupon, order, and order items."""
#         # Create a test user
#         self.user = User.objects.create_user(
#             username='testuser', password='testpassword', email='testemail@gmail.com',
#             first_name='testfirst', last_name='testlast', phone='999999999',
#             address='testadress'
#         )
#
#         # Create test category, color, size, quantity, product, and related objects
#         self.category = Category.objects.create(name='Gorros')
#         self.color = Color.objects.create(name='Red')
#         self.size = Size.objects.create(size='0-6 meses')
#         self.quantity = Quantity.objects.create(quantity=12)
#
#         self.product = Product.objects.create(
#             name='Test Gorro',
#             description='Exclusivo para tests',
#             price=Decimal('300.00'),
#             category=self.category
#         )
#
#         self.productcolor = ProductColor.objects.create(product=self.product, color=self.color)
#
#         self.product.colors.set([self.productcolor])
#         self.product.size.set([self.size])
#         self.product.quantity.set([self.quantity])
#
#         # Set up delivery and coupon details
#         self.delivery = Delivery.objects.create(place='testdelivery', cost=90)
#         self.coupon = Coupon.objects.create(code="DISCOUNT10",
#                                             valid_from=timezone.now().replace(year=timezone.now().year - 1),
#                                             valid_to=timezone.now().replace(year=timezone.now().year + 5),
#                                             discount=10,
#                                             active=True)
#         self.discount = self.coupon.discount
#
#         # Create an order and its item
#         self.order = Order.objects.create(
#             user=self.user,
#             first_name=self.user.first_name,
#             last_name=self.user.last_name,
#             email=self.user.email,
#             phone=self.user.phone,
#             address=self.user.address,
#             delivery=self.delivery,
#             coupon=self.coupon,
#             discount=self.discount,
#             language='es',
#         )
#
#         OrderItem.objects.create(
#             order=self.order,
#             product=self.product,
#             color=self.color,
#             size=self.size,
#             price=self.product.price,
#             product_quantity=2,
#         )
#
#         # Configure client for request-based tests
#         self.client = Client()
#         self.client.login(username='testuser', password='testpassword')
#
#     @patch('stripe.checkout.Session.create')
#     def test_payment_process_view_post(self, mock_stripe_session):
#         """Test POST request to payment process view with Stripe session creation."""
#         mock_stripe_session.return_value = MockStripeSession(id="test_session_id", url="https://stripe.com/test")
#
#         # Simulate session data with order ID
#         session = self.client.session
#         session['order_id'] = self.order.id
#         session.save()
#
#         response = self.client.post(reverse('payment:process'))
#         self.assertEqual(response.status_code, HTTPStatus.FOUND)
#         self.assertEqual(response.url, "https://stripe.com/test")
#
#         # Verify Stripe session creation with expected data
#         mock_stripe_session.assert_called_once()
#         session_data = mock_stripe_session.call_args[1]
#         self.assertEqual(session_data['client_reference_id'], self.order.id)
#         self.assertEqual(session_data['shipping_options'][0]['shipping_rate_data']['fixed_amount']['amount'], 9000)
#
#     def test_payment_process_view_get(self):
#         """Test GET request to payment process view for rendering correct template and data."""
#         session = self.client.session
#         session['order_id'] = self.order.id
#         session.save()
#
#         response = self.client.get(reverse('payment:process'))
#         self.assertEqual(response.status_code, HTTPStatus.OK)
#         self.assertTemplateUsed(response, 'payment/process.html')
#         self.assertContains(response, self.order.items.first().name)
#         self.assertContains(response, self.order.items.first().color)
#         self.assertContains(response, self.order.items.first().size)
#         self.assertContains(response, f'Cupón "{self.order.coupon.code}"')
#         self.assertContains(response, f'(-{self.discount}%)')
#
#     def test_payment_completed_view(self):
#         """Test the payment completed view for successful payment message."""
#         response = self.client.get(reverse('payment:completed'))
#         self.assertEqual(response.status_code, HTTPStatus.OK)
#         self.assertTemplateUsed(response, 'payment/completed.html')
#         self.assertContains(response, "Pago exitoso!")
#
#     def test_payment_canceled_view(self):
#         """Test the payment canceled view for failed payment message."""
#         response = self.client.get(reverse('payment:canceled'))
#         self.assertEqual(response.status_code, HTTPStatus.OK)
#         self.assertTemplateUsed(response, 'payment/canceled.html')
#         self.assertContains(response, "Hubo un problema al procesar su pago.")
#
#     def test_update_partial_payment_status_view_post(self):
#         """Test updating partial payment status through a JSON request."""
#         session = self.client.session
#         session['order_id'] = self.order.id
#         session.save()
#
#         response = self.client.post(reverse('payment:partial_payment_update'), {'partial_payment': 'true'},
#                                     content_type='application/json')
#         self.assertEqual(response.status_code, HTTPStatus.OK)
#         self.assertJSONEqual(response.content, {
#             'status': 'ok',
#             'partial_payment': True,
#             'total_cost': str(self.order.get_total_cost()),
#             'partial_payment_cost': str(self.order.get_total_cost_with_partial_payment())
#         })
#
#         # Confirm partial payment update in the database
#         self.order.refresh_from_db()
#         self.assertTrue(self.order.partial_payment)
#
#     def test_update_partial_payment_status_view_order_not_found(self):
#         """Test error response for an invalid order ID in partial payment update request."""
#         session = self.client.session
#         session['order_id'] = 999  # Invalid order ID
#         session.save()
#
#         response = self.client.post(reverse('payment:partial_payment_update'), {'partial_payment': 'true'},
#                                     content_type='application/json')
#         self.assertEqual(response.status_code, HTTPStatus.OK)
#         self.assertJSONEqual(response.content, {'status': 'error', 'message': 'Order not found'})
