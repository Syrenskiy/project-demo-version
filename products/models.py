import os
from xml.etree.ElementTree import parse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, MaxLengthValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import ManyToManyField, Min, F, Case, When, QuerySet
from django.urls import reverse
from django.utils import timezone
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, Transpose
from parler.managers import TranslatableManager
from parler.models import TranslatableModel, TranslatedFields, TranslationDoesNotExist

from django.core.files.uploadedfile import UploadedFile

from princesscastle.settings.storages import MediaStorage

from django.utils.translation import gettext_lazy as _


def validate_svg(value: UploadedFile) -> None:
    """
    Validates that the uploaded file is an SVG:
    - Checks the file extension is '.svg'.
    - Ensures the file content is valid XML (basis of SVG format).
    Raises ValidationError if the file is invalid.
    """
    ext = os.path.splitext(value.name)[1].lower()
    if ext != '.svg':
        raise ValidationError(_("El archivo debe tener la extensión '.svg'."))
    try:
        parse(value)
    except Exception:
        raise ValidationError(_("El archivo SVG no es válido."))


def validate_image_size(image: UploadedFile) -> None:
    """Image size validation"""
    max_size = 1 * 1024 * 1024
    if image.size > max_size:
        raise ValidationError(_('El tamaño de la imagen no debe superar 1 MB.'))


class PublishedManager(TranslatableManager):
    """Manager for retrieving only published products."""

    def get_queryset(self) -> QuerySet['Product']:
        return super().get_queryset().filter(is_published=Product.Status.PUBLISHED)

    def with_min_price(self) -> QuerySet['Product']:
        """
        Annotates the queryset with the minimum price.

        Adds:
        - min_size_price: Minimum price among product sizes.
        - min_quantity_price: Minimum price among product quantities.
        - min_price: Smallest of min_size_price, min_quantity_price, or the default price.

        Returns:
            QuerySet: Annotated queryset with min_price field.
        """
        return self.get_queryset().annotate(
            min_size_price=Min('productsize__price'),
            min_quantity_price=Min('productquantity__price'),
            min_price=Case(
                When(min_size_price__isnull=False, then=F('min_size_price')),
                When(min_quantity_price__isnull=False, then=F('min_quantity_price')),
                default=F('price'),
            )
        )


class Product(TranslatableModel):
    """Model representing a product with multilingual support and attributes like size, color, and category."""

    class Status(models.IntegerChoices):
        DRAFT = 0, 'Borrador'
        PUBLISHED = 1, 'Publicado'

    translations = TranslatedFields(
        name=models.CharField(max_length=100, verbose_name=_('Nombre')),
        slug=models.SlugField(max_length=100, unique=True, verbose_name=_('Slug'),
                              validators=[
                                  MinLengthValidator(5, message=_('Mínimo 5 caracteres')),
                                  MaxLengthValidator(100, message=_('Máximo 100 caracteres')),
                              ]),
        description=models.TextField(blank=True, verbose_name=_('Descripción')),
    )
    image = models.ImageField(upload_to='images/products/', verbose_name=_('Imagen'),
                              validators=[validate_image_size])
    image_1x1 = ImageSpecField(source='image', processors=[Transpose(), ResizeToFill(200, 200)],
                               format='JPEG', options={'quality': 70})
    image_3x4 = ImageSpecField(source='image', processors=[Transpose(), ResizeToFill(240, 320)],
                               format='JPEG', options={'quality': 60})
    image_3x4_150x200 = ImageSpecField(source='image', processors=[Transpose(), ResizeToFill(150, 200)],
                                       format='JPEG', options={'quality': 70})
    image_3x4_120x160 = ImageSpecField(source='image', processors=[Transpose(), ResizeToFill(120, 160)],
                                       format='JPEG', options={'quality': 80})
    category = models.ForeignKey('Category', on_delete=models.PROTECT,
                                 related_name='products', verbose_name=_('Categoría'))
    tags = models.ManyToManyField('Tag', related_name='products', blank=True, verbose_name=_('Tags'))
    size = models.ManyToManyField('Size', related_name='products', blank=True,
                                  through='ProductSize', verbose_name=_('Talla'))
    quantity = models.ManyToManyField('Quantity', related_name='products', blank=True,
                                      through='ProductQuantity', verbose_name=_('Cantidad'))
    price = models.DecimalField(max_digits=10, decimal_places=2,
                                blank=True, null=True, verbose_name=_('Precio'))
    is_published = models.IntegerField(choices=Status.choices, default=Status.DRAFT,
                                       verbose_name=_('Estado'))
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='products', blank=True, verbose_name='Likes')

    # Managers for product query customization
    objects = TranslatableManager()
    published = PublishedManager()

    class Meta:
        verbose_name = _('Productos')
        verbose_name_plural = _('Productos')

    def __str__(self):
        try:
            return self.name
        except TranslationDoesNotExist:
            return ''

    def get_absolute_url(self):
        """Returns the URL for this product based on its category and color."""
        first_color = self.colors.all()[0]

        return reverse('product', kwargs={
            'category_slug': self.category.slug,
            'product_slug': self.slug,
            'color_slug': first_color.color.slug
        })


class Tag(TranslatableModel):
    """Model representing tags with translations, used to categorize products."""
    translations = TranslatedFields(
        name=models.CharField(max_length=100, unique=True, verbose_name=_('Tag')),
        slug=models.SlugField(max_length=100, unique=True, verbose_name=_('Slug')),
    )

    class Meta:
        verbose_name = _('Etiqueta')
        verbose_name_plural = _('Etiquetas')

    def __str__(self):
        try:
            return self.name
        except TranslationDoesNotExist:
            return ''

    def get_absolute_url(self):
        return reverse('tag', kwargs={'tag_slug': self.slug})


class Image(models.Model):
    """Model for storing images associated with specific product colors."""
    product_color = models.ForeignKey('ProductColor', on_delete=models.PROTECT, blank=True, null=True,
                                      related_name='images', verbose_name=_('Color'))
    image = models.ImageField(upload_to='images/product_color/', blank=True, null=True,
                              verbose_name=_('Imagen'), validators=[validate_image_size])
    image_product = ImageSpecField(source='image', processors=[Transpose(), ResizeToFill(600, 600)],
                                   format='JPEG', options={'quality': 70})

    class Meta:
        verbose_name = _('Imagen')
        verbose_name_plural = _('Imágenes')

    def __str__(self):
        return (_('Imagen %(product_color_color_name)s para %(product_color_product_name)s')
                % {'product_color_color_name': self.product_color.color.name,
                   'product_color_product_name': self.product_color.product.name})


class Category(TranslatableModel):
    """Model representing a product category with translations."""
    translations = TranslatedFields(
        name=models.CharField(max_length=100, unique=True, verbose_name=_('Categoría')),
        slug=models.SlugField(max_length=100, unique=True, verbose_name=_('Slug')),
    )

    class Meta:
        verbose_name = _('Categoría')
        verbose_name_plural = _('Categorías')

    def __str__(self):
        try:
            return self.name
        except TranslationDoesNotExist:
            return ''

    def get_absolute_url(self):
        return reverse('category', kwargs={'category_slug': self.slug})


class ThematicCategory(TranslatableModel):
    """Model representing a thematic product category with translations."""
    translations = TranslatedFields(
        name=models.CharField(max_length=100, unique=True, verbose_name=_('Categoría temática')),
        slug=models.SlugField(max_length=100, unique=True, verbose_name=_('Slug')),
    )
    image = models.ImageField(upload_to='images/thematic_category/', blank=True, null=True)
    image_thematic = ImageSpecField(source='image', processors=[Transpose(), ResizeToFill(150, 150)],
                                    format='JPEG', options={'quality': 70})
    products = models.ManyToManyField('Product', related_name='thematic_categories',
                                      verbose_name=_('Productos'))
    valid_from = models.DateTimeField(verbose_name='Válido desde')
    valid_to = models.DateTimeField(verbose_name='Válido hasta')

    class Meta:
        verbose_name = _('Categoría temática')
        verbose_name_plural = _('Categorías temáticas')

    def __str__(self):
        try:
            return self.name
        except TranslationDoesNotExist:
            return ''

    def is_active(self) -> bool:
        """Checks if the thematic category is currently active based on date range and products."""
        now = timezone.now()
        published_products_exists = self.products.filter(is_published=Product.Status.PUBLISHED).exists()
        return self.valid_from <= now <= self.valid_to and published_products_exists

    def get_absolute_url(self):
        return reverse('thematic_category', kwargs={'thematic_category_slug': self.slug})


class Color(TranslatableModel):
    """Model representing product colors with translations icons."""
    translations = TranslatedFields(
        name=models.CharField(max_length=30, unique=True, verbose_name=_('Color')),
        slug=models.SlugField(max_length=30, unique=True, verbose_name=_('Slug')),
    )
    icon = models.FileField(upload_to='images/icons/colors/svg/', verbose_name=_('Icono'),
                            validators=[validate_svg])

    class Meta:
        verbose_name = _('Color')
        verbose_name_plural = _('Colores')

    def __str__(self):
        try:
            return self.name
        except TranslationDoesNotExist:
            return ''


class ProductColor(models.Model):
    """Intermediate model representing the relationship between a product and a color."""
    product = models.ForeignKey('Product', on_delete=models.DO_NOTHING, related_name='colors',
                                verbose_name=_('Producto'))
    color = models.ForeignKey('Color', on_delete=models.DO_NOTHING, related_name='colors',
                              verbose_name=_('Color'))

    class Meta:
        unique_together = ('product', 'color')
        verbose_name = _('Producto + Color')
        verbose_name_plural = _('Productos + Colores')

    def __str__(self):
        return self.product.name + '_' + self.color.name


class Quantity(models.Model):
    """Model representing available quantities for products."""
    quantity = models.CharField(max_length=10, verbose_name=_('Cantidad'))
    slug = models.SlugField(max_length=10, unique=True, verbose_name=_('Slug'))

    class Meta:
        verbose_name = _('Cantidad')
        verbose_name_plural = _('Cantidades')

    def __str__(self):
        return self.quantity


class ProductQuantity(models.Model):
    """Intermediate model representing the relationship between a product and a quantity."""
    product = models.ForeignKey('Product', on_delete=models.DO_NOTHING, verbose_name=_('Producto'))
    quantity = models.ForeignKey('Quantity', on_delete=models.DO_NOTHING, related_name='productquantity',
                                 verbose_name=_('Cantidad'))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Precio'))

    class Meta:
        unique_together = ('product', 'quantity')
        verbose_name = _('Producto + Cantidad')
        verbose_name_plural = _('Productos + Cantidades')

    def __str__(self):
        return self.product.name + '_' + self.quantity.quantity


class Size(TranslatableModel):
    """Model representing product sizes with translations."""
    translations = TranslatedFields(
        size=models.CharField(max_length=30, verbose_name=_('Talla')),
        slug=models.SlugField(max_length=30, unique=True, verbose_name=_('Slug')),
    )

    class Meta:
        verbose_name = _('Talla')
        verbose_name_plural = _('Tallas')

    def __str__(self):
        try:
            return self.size
        except TranslationDoesNotExist:
            return ''


class ProductSize(models.Model):
    """Intermediate model representing the relationship between a product and a size."""
    product = models.ForeignKey('Product', on_delete=models.DO_NOTHING, verbose_name=_('Producto'))
    size = models.ForeignKey('Size', on_delete=models.DO_NOTHING, related_name='productsize',
                             verbose_name=_('Talla'))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Precio'))

    class Meta:
        unique_together = ('product', 'size')
        verbose_name = _('Producto + Talla')
        verbose_name_plural = _('Productos + Tallas')

    def __str__(self):
        return self.product.name + '_' + self.size.size


class Comment(models.Model):
    """Model for storing user comments on products, including rating and active status."""
    product = models.ForeignKey('Product', on_delete=models.CASCADE,
                                related_name='comments', verbose_name=_('Producto'))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='comments',
                             on_delete=models.DO_NOTHING, verbose_name=_('Usuario'))
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name=_('Rating')
    )
    comment = models.TextField(max_length=300, verbose_name=_('Comentario'))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha'))
    active = models.BooleanField(default=True, verbose_name=_('Activo'))

    class Meta:
        ordering = ['-created']
        indexes = [models.Index(fields=['-created'])]
        verbose_name = _('Comentario')
        verbose_name_plural = _('Comentarios')

    def __str__(self):
        return (_('Comentario de %(user)s de producto %(product)s')
                % {'user': self.user, 'product': self.product})


class ProductSuggestion(models.Model):
    """Model for storing user suggestions including description and images."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
                             verbose_name=_('Usuario'))
    phone = models.CharField(max_length=50, verbose_name=_('Teléfono'))
    description = models.TextField(verbose_name=_('Descripción'))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Creado'))

    def __str__(self):
        return f'Propuesta de usuario {self.user}, creada {self.created}'


class ProductSuggestionImage(models.Model):
    """A model for storing images attached to suggestions."""
    suggestion = models.ForeignKey('ProductSuggestion', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='images/suggestion_images/', blank=True, null=True)
