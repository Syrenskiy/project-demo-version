from decimal import Decimal
from http import HTTPStatus

from django.test import TestCase

from django.urls import reverse
from django.utils import translation
from django.utils.translation import activate

from products.models import Product, Category, Size, Tag, ProductColor, Color, Quantity


class ProductViewsTest(TestCase):
    """Test suite for product views in the products app."""
    def setUp(self):
        """Set up initial test data for categories, products, colors, sizes, etc."""
        self.category = Category.objects.create()
        self.color = Color.objects.create(icon='/media/images/colors/2024/10/22')
        self.size = Size.objects.create()
        self.quantity = Quantity.objects.create(quantity=12)

        self.product = Product.objects.create(
            price=Decimal('300.00'),
            category=self.category,
            is_published=Product.Status.PUBLISHED
        )

        # Set product and related models' translations for Spanish
        with translation.override('es'):
            self.product.set_current_language('es')
            self.product.name = "Test Gorro"
            self.product.slug = "test-gorro"
            self.product.description = "Exclusivo para tests"
            self.product.save()

            self.category.set_current_language('es')
            self.category.name = 'Gorros'
            self.category.slug = 'gorros'
            self.category.save()

            self.color.set_current_language('es')
            self.color.name = 'Rojo'
            self.color.slug = 'rojo'
            self.color.save()

            self.size.set_current_language('es')
            self.size.name = '0-6 meses'
            self.size.slug = '0-6-meses'
            self.size.save()

        self.productcolor = ProductColor.objects.create(product=self.product, color=self.color)

        # Associate colors, sizes, and quantity with the product
        self.product.colors.set([self.productcolor])
        self.product.size.set([self.size])
        self.product.quantity.set([self.quantity])

    def test_product_translation(self):
        """Ensure product translations are correctly set and accessible."""
        with translation.override('es'):
            self.product.set_current_language('es')
            self.assertEqual(self.product.name, "Test Gorro")
            self.assertEqual(self.product.slug, "test-gorro")

    def test_products_home_view(self):
        """Verify that the home view loads correctly and includes the product."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'products/index.html')
        self.assertIn(self.product, response.context['products'])

    def test_product_category_view(self):
        """Verify that products in a specific category are retrieved correctly."""
        activate('es')
        response = self.client.get(reverse('category', kwargs={'category_slug': self.category.slug}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(self.product, response.context['products'])

    def test_product_detail_view(self):
        """Ensure product detail view loads and template is used correctly."""
        response = self.client.get(reverse('product', kwargs={
            'category_slug': self.category.slug,
            'product_slug': self.product.slug,
            'color_slug': self.product.colors.first().color.slug
        }))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'products/product.html')

    def test_product_unpublished(self):
        """Check that unpublished products do not appear in the published list."""
        self.product.is_published = Product.Status.DRAFT
        self.product.save()
        unpublished_products = Product.published.all()
        self.assertNotIn(self.product, unpublished_products)

    def test_product_absolute_url(self):
        """Verify that the product's absolute URL includes its slug."""
        url = self.product.get_absolute_url()
        self.assertIn(self.product.slug, url)
