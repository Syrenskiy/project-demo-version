from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal

from django.utils import timezone

from coupons.models import Coupon
from orders.models import Order, OrderItem, Delivery
from products.models import Product, Category, Size, Color, Quantity, ProductColor


User = get_user_model()


class OrderTests(TestCase):
    """
    Test suite for Order and OrderItem functionalities, covering creation,
    form submission, and order data validation.
    """

    def setUp(self):
        """Set up a test user and associated objects for testing order creation"""
        self.user = User.objects.create_user(
            username='testuser', password='testpassword', email='testemail@gmail.com',
            first_name='testfirst', last_name='testlast', phone='999999999',
            address='testadress'
        )

        self.category = Category.objects.create(name='Gorros')
        self.color = Color.objects.create(name='Red')
        self.size = Size.objects.create(size='0-6 meses')
        self.quantity = Quantity.objects.create(quantity=12)

        self.product = Product.objects.create(
            name='Test Gorro',
            description='Exclusivo para tests',
            price=Decimal('300.00'),
            category=self.category
        )

        self.productcolor = ProductColor.objects.create(product=self.product, color=self.color)

        self.product.colors.set([self.productcolor])
        self.product.size.set([self.size])
        self.product.quantity.set([self.quantity])

        self.delivery = Delivery.objects.create(place='testdelivery', cost=90)

        self.client = Client()
        self.client.login(username='testuser', password='testpassword')

        # Create a test coupon with a 10% discount
        self.coupon = Coupon.objects.create(code="DISCOUNT10",
                                            valid_from=timezone.now().replace(year=timezone.now().year - 1),
                                            valid_to=timezone.now().replace(year=timezone.now().year + 5),
                                            discount=10,
                                            active=True)
        self.discount = self.coupon.discount

    def test_order_creation(self):
        """
        Tests that an order and its associated items can be successfully created and
        saved to the database, and that the total cost is calculated accurately.
        """
        order = Order.objects.create(
            user=self.user,
            first_name=self.user.first_name,
            last_name=self.user.last_name,
            email=self.user.email,
            phone=self.user.phone,
            address=self.user.address,
            delivery=self.delivery,
            coupon=self.coupon,
            discount=self.discount,
            language='es',
        )

        OrderItem.objects.create(
            order=order,
            product=self.product,
            color=self.color,
            size=self.size,
            price=self.product.price,
            product_quantity=2,
        )

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.get_total_cost(), Decimal('630.00'))

    def test_order_form(self):
        """
        Verifies the order creation process via the order form, ensuring that a POST
        request successfully creates an order and redirects to the payment process.
        """

        url = reverse('orders:order_create')
        response = self.client.post(url, {
            'user': self.user,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'email': self.user.email,
            'phone': self.user.phone,
            'address': self.user.address,
            'delivery': self.delivery.id,
        })

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, reverse('payment:process'))

        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.user, self.user)


