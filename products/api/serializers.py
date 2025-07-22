from rest_framework import serializers

from products.models import Product, Category, Tag, Size, Quantity, Comment, Color, ProductColor


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['slug', 'name']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['slug', 'name']


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'rating', 'comment', 'created']


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    size_prices = serializers.SerializerMethodField()
    quantity_prices = serializers.SerializerMethodField()
    colors_images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'min_price',
                  'size_prices', 'quantity_prices',
                  'colors_images', 'category', 'description',
                  'image', 'tags', 'comments']

    def get_comments(self, obj: Product):
        """Return only active comments for the product."""
        active_comments = obj.comments.filter(active=True)
        return CommentSerializer(active_comments, many=True).data

    def get_size_prices(self, obj: Product):
        """Return sizes and their prices for the product."""
        size_prices = obj.productsize_set.all()
        return [
            {'slug': size.size.slug, 'size': size.size.size, 'price': size.price}
            for size in size_prices
        ]

    def get_quantity_prices(self, obj: Product):
        """Return quantities and their prices for the product."""
        quantity_prices = obj.productquantity_set.all()
        return [
            {'slug': quantity.quantity.quantity, 'quantity': quantity.quantity.quantity,
             'price': quantity.price} for quantity in quantity_prices
        ]

    def get_min_price(self, obj):
        return getattr(obj, 'min_price', None)

    def get_colors_images(self, obj: ProductColor):
        """Return colors, their slugs, icons, and associated images with absolute URLs for the product."""
        request = self.context.get('request')
        colors = obj.colors.all()
        return [
            {'slug': color.color.slug, 'color': color.color.name, 'icon': color.color.icon.url,
             'images': [request.build_absolute_uri(image.image.url) for image in color.images.all() if image.image]}
            for color in colors
        ]