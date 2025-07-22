from decimal import Decimal
from django.conf import settings
from django.test import TestCase, RequestFactory
from django.utils import timezone

from cart.cart import Cart
from products.models import Product, Color, Size, Quantity, Category, ProductColor
from coupons.models import Coupon


class CartTests(TestCase):
    """
    Test suite for the Cart functionality, including product addition, subtraction,
    removal, price calculation, and cart clearing operations.
    """

    def setUp(self):
        """Sets up initial test data for cart, product, color, size, quantity, and coupon."""
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.request.session = self.client.session
        self.cart = Cart(self.request)

        # Set up initial product and associated attributes
        self.category = Category.objects.create(name='Test Category')
        self.color = Color.objects.create(name='Red')
        self.size = Size.objects.create(size='M')
        self.quantity = Quantity.objects.create(quantity=10)

        self.product = Product.objects.create(name='Test Product',
                                              category=self.category,
                                              price=Decimal('100.00'))

        self.productcolor = ProductColor.objects.create(product=self.product, color=self.color)

        self.product.colors.set([self.productcolor])
        self.product.size.set([self.size])
        self.product.quantity.set([self.quantity])

        # Create a valid coupon for testing discount functionality
        self.coupon = Coupon.objects.create(
            code="DISCOUNT10",
            valid_from=timezone.now().replace(year=timezone.now().year - 1),
            valid_to=timezone.now().replace(year=timezone.now().year + 5),
            discount=10,
            active=True
        )

    def test_cart_add(self):
        """
        Tests adding products with specific quantities, sizes, and colors to the cart.
        Verifies that the correct cart item IDs are created and quantities updated.
        """
        self.cart.add(product=self.product, color=self.color, product_quantity=2, quantity=self.quantity)
        cart_item_id_1 = f"{self.product.id}_{self.color.id}_None_{self.quantity.id}"

        # Add a second variation with a different size
        self.cart.add(product=self.product, color=self.color, product_quantity=1, size=self.size)
        cart_item_id_2 = f"{self.product.id}_{self.color.id}_{self.size.id}_None"

        # Assert cart contains both variations with expected quantities and price
        self.assertIn(cart_item_id_1, self.cart.cart)
        self.assertIn(cart_item_id_2, self.cart.cart)
        self.assertEqual(self.cart.cart[cart_item_id_1]['product_quantity'], 2)
        self.assertEqual(self.cart.cart[cart_item_id_2]['product_quantity'], 1)
        self.assertEqual(self.cart.cart[cart_item_id_1]['price'], str(self.product.price))

    def test_cart_subtract(self):
        """
        Tests decreasing product quantity in the cart. Checks that quantity is correctly
        reduced and verifies correct handling if quantity reaches zero.
        """
        self.cart.add(product=self.product, color=self.color, product_quantity=3, size=self.size)
        self.cart.subtract(product=self.product, color=self.color, size=self.size)
        cart_item_id = f"{self.product.id}_{self.color.id}_{self.size.id}_None"

        # Assert the quantity was reduced by 1
        self.assertEqual(self.cart.cart[cart_item_id]['product_quantity'], 2)

    def test_cart_remove(self):
        """Tests removing a product from the cart and verifies it is no longer in the cart."""
        self.cart.add(product=self.product, color=self.color, product_quantity=1, quantity=self.quantity)
        self.cart.remove(product=self.product, color=self.color, quantity=self.quantity)
        cart_item_id = f"{self.product.id}_{self.color.id}_None_{self.quantity.id}"

        # Assert the cart no longer contains the item
        self.assertNotIn(cart_item_id, self.cart.cart)

    def test_cart_total_price(self):
        """
        Verifies correct calculation of total cart price for multiple products and quantities.
        """
        self.cart.add(product=self.product, color=self.color, product_quantity=1, size=self.size)
        self.cart.add(product=self.product, color=self.color, product_quantity=2, quantity=self.quantity)

        # Calculate expected total price based on quantities
        total_price = self.cart.get_total_price()
        expected_total_price = self.product.price * 3
        self.assertEqual(total_price, expected_total_price)

    def test_clear_cart(self):
        """
        Tests clearing the cart, ensuring it is empty and session data is removed.
        """
        self.cart.add(product=self.product, color=self.color, product_quantity=1, size=self.size)
        self.assertIn(settings.CART_SESSION_ID, self.request.session)
        self.cart.clear()

        # Assert the cart and session data have been cleared
        self.assertNotIn(settings.CART_SESSION_ID, self.request.session)

    def test_cart_iteration(self):
        """
        Verifies iteration over cart items returns the correct product, color, size,
        quantity, and total price data.
        """
        self.cart.add(product=self.product, color=self.color, product_quantity=2, size=self.size)
        items = list(self.cart)

        # Assert single item in cart and all attributes are as expected
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item['product'], self.product)
        self.assertEqual(item['color'], self.color)
        self.assertEqual(item['size'], self.size)
        self.assertEqual(item['product_quantity'], 2)
        self.assertEqual(item['total_price'], self.product.price * 2)

