import copy
from decimal import Decimal
from django.conf import settings
from django.db.models import Prefetch

from coupons.models import Coupon
from products.models import Product, ProductColor


class Cart:
    """
    A class representing the user's shopping cart, with support for
    adding, subtracting, and removing items, as well as handling discounts.
    """

    def __init__(self, request):
        """Initializes the cart instance with the session data."""
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        self.coupon_id = self.session.get('coupon_id')

    @staticmethod
    def get_cart_item_id_and_others(product, color, size=None, quantity=None):
        """Generates a unique cart item ID based on product attributes."""
        product_id = product.id
        color_id = color.id
        size_id = size.id if size else None
        quantity_id = quantity.id if quantity else None

        cart_item_id = f"{product_id}_{color_id}_{size_id}_{quantity_id}"

        cart_item = {
            'cart_item_id': cart_item_id,
            'product_id': product_id,
            'color_id': color_id,
            'size_id': size_id,
            'quantity_id': quantity_id
        }

        return cart_item

    def add(self, product, color, price, product_quantity=1, size=None, quantity=None):
        """Adds a product to the cart or updates its quantity if it already exists."""
        item = self.get_cart_item_id_and_others(product, color, size=size, quantity=quantity)

        cart_item = self.cart.get(item['cart_item_id'], {
            'product_quantity': 0,
            'price': str(price),
        })
        cart_item['product_quantity'] += product_quantity
        cart_item['product_id'] = item['product_id']
        cart_item['color_id'] = item['color_id']
        cart_item['size_id'] = item['size_id']
        cart_item['quantity_id'] = item['quantity_id']

        self.cart[item['cart_item_id']] = cart_item
        self.save()

    def update(self, product, color, price, size=None, quantity=None):
        """Update the price of an item in the cart."""
        item = self.get_cart_item_id_and_others(product, color, size=size, quantity=quantity)

        cart_item_id = item['cart_item_id']

        if cart_item_id in self.cart:
            self.cart[cart_item_id]['price'] = str(price)
            self.save()

    def subtract(self, product, color, size=None, quantity=None):
        """Subtracts a quantity from an item in the cart or removes it if quantity reaches zero."""
        item = self.get_cart_item_id_and_others(product, color, size=size, quantity=quantity)

        cart_item_id = item['cart_item_id']

        if self.cart[cart_item_id]['product_quantity'] == 1:
            self.remove(product=product, color=color, size=size, quantity=quantity)
        else:
            self.cart[cart_item_id]['product_quantity'] -= 1
            self.save()

    def remove(self, product, color, size=None, quantity=None):
        """Remove an item from the cart by ID."""
        item = self.get_cart_item_id_and_others(product, color, size=size, quantity=quantity)

        cart_item_id = item['cart_item_id']

        if cart_item_id in self.cart:
            del self.cart[cart_item_id]
            self.save()

    def save(self):
        """Marks the session as modified to ensure cart updates are saved."""
        self.session.modified = True

    def __iter__(self):
        """Iterates over cart items, yielding item data with associated product details."""
        product_ids = {item['product_id'] for item in self.cart.values()}

        products = (Product.objects
        .filter(id__in=product_ids)
        .select_related('category')
        .prefetch_related(
            Prefetch('colors', queryset=ProductColor.objects.prefetch_related('color__translations').order_by('id')),
            'size',
            'quantity',
            'translations',
            'category__translations'
        )
        )

        cart = copy.deepcopy(self.cart)
        sorted_cart_items = sorted(cart.items())

        for item_id, item in sorted_cart_items:
            product = next((p for p in products if p.id == item['product_id']), None)

            if product:
                item['product'] = product

                product_color = next(
                    (color_instance for color_instance in product.colors.all()
                     if color_instance.color.id == item['color_id']), None)
                item['color'] = product_color.color if product_color else None

                size = next((size for size in product.size.all() if size.id == item['size_id']), None)
                item['size'] = size

                quantity = next((quantity for quantity in product.quantity.all() if quantity.id == item['quantity_id']),
                                None)
                item['quantity'] = quantity

                item['price'] = Decimal(item['price'])
                item['total_price'] = item['price'] * item['product_quantity']
                yield item

    def __len__(self):
        """Returns the total number of items in the cart."""
        return sum(item['product_quantity'] for item in self.cart.values())

    def get_total_price(self):
        """Calculates the total price of all items in the cart."""
        return sum(
            Decimal(item['price']) * item['product_quantity']
            for item in self.cart.values()
        )

    def clear(self):
        """Clears all items from the cart and removes any applied coupon."""
        del self.session[settings.CART_SESSION_ID]
        self.session['coupon_id'] = None
        self.save()

    @property
    def coupon(self):
        """Retrieve applied coupon if exists."""
        if not hasattr(self, '_cached_coupon'):
            if self.coupon_id:
                try:
                    self._cached_coupon = Coupon.objects.get(id=self.coupon_id)
                except Coupon.DoesNotExist:
                    self._cached_coupon = None
            else:
                self._cached_coupon = None
        return self._cached_coupon

    @coupon.setter
    def coupon(self, value):
        """Set or remove the coupon."""
        if value is None:
            self.session.pop('coupon_id', None)
        else:
            self.session['coupon_id'] = value.id

        self._cached_coupon = value
        self.save()

    def get_discount(self):
        """Calculate discount based on applied coupon."""
        if self.coupon:
            return self.coupon.discount / Decimal(100) * self.get_total_price()
        return Decimal(0)

    def get_total_price_after_discount(self):
        """Calculate total price after applying discount."""
        return self.get_total_price() - self.get_discount()
