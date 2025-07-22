from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from .models import Product, Category, Tag, Comment
from django.contrib.auth import get_user_model

User = get_user_model()


class ProductAPITests(APITestCase):
    """Test suite for the Product API endpoints."""
    def setUp(self):
        """Set up test client and initial data for products, categories, and tags."""
        self.client = APIClient()
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.tag = Tag.objects.create(name="Popular", slug="popular")
        self.product = Product.published.create(
            name="Smartphone",
            slug="smartphone",
            description="Latest model",
            price="999.99",
            category=self.category,
            is_published=Product.Status.PUBLISHED,
        )
        self.product.tags.add(self.tag)
        self.product_url = reverse('products:product-detail', args=[self.product.id])

    def test_list_products(self):
        """Test retrieving the list of products."""
        url = reverse('products:product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_retrieve_product(self):
        """Test retrieving details of a single product."""
        response = self.client.get(self.product_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.product.id)
        self.assertEqual(response.data['name'], self.product.name)
        self.assertEqual(response.data['category']['name'], self.category.name)

    def test_filter_products_by_category(self):
        """Test filtering products by category ID."""
        url = f"{reverse('products:product-list')}?category={self.category.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(prod['category']['id'] == self.category.id for prod in response.data['results']))

    def test_filter_products_by_tag(self):
        """Test filtering products by tag ID."""
        url = f"{reverse('products:product-list')}?tags={self.tag.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(self.tag.name in [tag['name'] for tag in prod['tags']] for prod in response.data['results']))

    def test_product_pagination(self):
        """Test pagination of the product list, with page size set to 1."""
        url = f"{reverse('products:product-list')}?page_size=1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_product_ordering(self):
        """Test ordering of products by price."""
        url = f"{reverse('products:product-list')}?ordering=price"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_comment_on_product(self):
        """Test retrieval of comments associated with a product."""
        user = User.objects.create(username='testuser')
        comment = Comment.objects.create(
            product=self.product,
            user=user,
            rating=5,
            comment="Great product!",
            active=True
        )
        response = self.client.get(self.product_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['comments']), 1)
        self.assertEqual(response.data['comments'][0]['comment'], comment.comment)


class CategoryAPITests(APITestCase):
    """Test suite for the Category API endpoints."""
    def setUp(self):
        """Set up test data for categories."""
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.category_url = reverse('products:category-detail', args=[self.category.id])

    def test_list_categories(self):
        """Test retrieving the list of categories."""
        url = reverse('products:category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_retrieve_category(self):
        """Test retrieving details of a single category."""
        response = self.client.get(self.category_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.category.id)
        self.assertEqual(response.data['name'], self.category.name)


class TagAPITests(APITestCase):
    """Test suite for the Tag API endpoints."""
    def setUp(self):
        """Set up test data for tags."""
        self.tag = Tag.objects.create(name="Popular", slug="popular")
        self.tag_url = reverse('products:tag-detail', args=[self.tag.id])

    def test_list_tags(self):
        """Test retrieving the list of tags."""
        url = reverse('products:tag-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_retrieve_tag(self):
        """Test retrieving details of a single tag."""
        response = self.client.get(self.tag_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.tag.id)
        self.assertEqual(response.data['name'], self.tag.name)
