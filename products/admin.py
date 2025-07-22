from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from parler.admin import TranslatableAdmin

from products.models import Product, Image, Tag, Color, Category, Quantity, Size, ProductColor, Comment, \
    ThematicCategory, ProductSuggestion, ProductSuggestionImage, ProductQuantity, ProductSize


class ImageInline(admin.TabularInline):
    """Inline admin for product images."""
    model = Image
    extra = 1


class ProductColorInline(admin.TabularInline):
    """Inline admin for product colors."""
    model = ProductColor
    extra = 1
    inlines = [ImageInline]


class ProductQuantityInline(admin.TabularInline):
    """Inline admin for product quantities."""
    model = ProductQuantity
    extra = 1


class ProductSizeInline(admin.TabularInline):
    """Inline admin for product sizes."""
    model = ProductSize
    extra = 1


@admin.register(Product)
class ProductAdmin(TranslatableAdmin):
    """Admin interface configuration for Product model."""
    list_display = ('name', 'display_image', 'category', 'price', 'is_published', 'display_likes')
    list_display_links = ['name']
    list_editable = ['is_published']
    actions = ['set_published', 'set_draft']
    list_per_page = 10
    list_filter = ['category', 'is_published']
    search_fields = ['name']
    inlines = [ProductColorInline, ProductQuantityInline, ProductSizeInline]
    show_facets = admin.ShowFacets.ALWAYS
    fields = ['name', 'slug', 'description', 'category',
              'tags', 'price', 'is_published', 'display_image', 'image']
    readonly_fields = ['display_image']
    filter_horizontal = ['tags']
    save_on_top = True

    def get_prepopulated_fields(self, request, obj=None):
        """Auto-populates the slug field based on the name field."""
        return {'slug': ('name',)}

    @admin.display(description='Imágen')
    def display_image(self, product: Product):
        """Displays a thumbnail image in the admin interface."""
        if product.image:
            return mark_safe(
                f"<a href='{product.image.url}'><img src='{product.image.url}' alt='{product.name}' width='50'></a>")

    @admin.display(description='Likes')
    def display_likes(self, product: Product):
        """Displays the count of likes for the product."""
        likes_count = product.likes.count()
        return likes_count if likes_count else None

    @admin.action(description='Publicar artículos seleccionados')
    def set_published(self, request, queryset):
        """Bulk action to mark products as published."""
        count = queryset.update(is_published=Product.Status.PUBLISHED)
        self.message_user(request, f'{count} artículos fueron publicados.')

    @admin.action(description='Quitar de publicados artículos seleccionados')
    def set_draft(self, request, queryset):
        """Bulk action to mark products as draft."""
        count = queryset.update(is_published=Product.Status.DRAFT)
        self.message_user(request, f'{count} artículos fueron pausados.')


class MixinAdmin(TranslatableAdmin):
    """Mixin class to configure common admin fields and options for related models."""
    list_display = ('name', 'slug', 'currently_in_use')
    list_display_links = ('name', 'slug')
    list_per_page = 10
    search_fields = ['name']

    def get_prepopulated_fields(self, request, obj=None):
        """Auto-populates the slug field based on the name field."""
        return {'slug': ('name',)}

    def get_queryset(self, request):
        """Annotates queryset with the count of associated products or colors."""
        queryset = super().get_queryset(request)
        if self.model == Color:
            queryset = queryset.annotate(product_count=Count('colors'))
        else:
            queryset = queryset.annotate(product_count=Count('products'))

        return queryset

    @admin.display(description='Vinculados', ordering='product_count')
    def currently_in_use(self, obj):
        """Displays the count of associated products or colors."""
        return obj.product_count


# Registering admin configurations for Category, Tag, Color, and other models
@admin.register(Category)
class CategoryAdmin(MixinAdmin):
    pass


@admin.register(Tag)
class TagAdmin(MixinAdmin):
    pass


@admin.register(ThematicCategory)
class ThematicCategoryAdmin(MixinAdmin):
    list_display = ('name', 'display_image', 'valid_from', 'valid_to', 'currently_in_use', 'display_is_active')
    list_display_links = ['name']
    fields = ['name', 'slug', 'display_image', 'image', 'valid_from', 'valid_to', 'products']
    readonly_fields = ['display_image']
    filter_horizontal = ['products']
    save_on_top = True

    @admin.display(description='Imágen')
    def display_image(self, thematic_category: ThematicCategory):
        """Displays a thumbnail image in the admin interface."""
        if thematic_category.image:
            return mark_safe(
                f"<a href='{thematic_category.image.url}'>"
                f"<img src='{thematic_category.image.url}' alt='{thematic_category.name}' width='70'></a>"
            )

    @admin.display(description='Activa', boolean=True)
    def display_is_active(self, obj):
        """Displays if the thematic category is active."""
        return obj.is_active()


@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    """Admin configuration for ProductColor model with Image inline."""
    list_display = ['product', 'color', 'total_images']
    inlines = [ImageInline]
    list_filter = ['product', 'color']
    list_per_page = 10

    def get_queryset(self, request):
        """Annotates queryset with the count of associated photos."""
        queryset = super().get_queryset(request).select_related('product', 'color').prefetch_related('images')

        queryset = queryset.annotate(photos_count=Count('images'))

        return queryset

    @admin.display(description='Cantidad de Fotos', ordering='photos_count')
    def total_images(self, obj):
        """Displays the count of associated photos."""
        return obj.photos_count


@admin.register(ProductQuantity)
class ProductQuantityAdmin(admin.ModelAdmin):
    """Admin configuration for ProductQuantity model."""
    pass


@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    """Admin configuration for ProductSize model."""
    pass


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    pass


@admin.register(Color)
class ColorAdmin(MixinAdmin):
    pass


@admin.register(Quantity)
class QuantityAdmin(admin.ModelAdmin):
    """Admin configuration for Quantity model."""
    list_display = ('quantity', 'slug')
    list_display_links = ('quantity', 'slug')
    list_per_page = 10
    prepopulated_fields = {'slug': ('quantity',)}
    search_fields = ['quantity']


@admin.register(Size)
class SizeAdmin(TranslatableAdmin):
    """Admin configuration for Size model."""
    list_display = ('size', 'slug')
    list_display_links = ('size', 'slug')
    list_per_page = 10
    search_fields = ['size']

    def get_prepopulated_fields(self, request, obj=None):
        """Auto-populates the slug field based on the size field."""
        return {'slug': ('size',)}


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin configuration for Comment model."""
    list_display = ('user', 'product', 'comment', 'created', 'active')
    list_editable = ['active']
    list_per_page = 10
    list_filter = ('user', 'product', 'created', 'active')
    search_fields = ('user', 'product', 'comment', 'created')
    show_facets = admin.ShowFacets.ALWAYS


class ProductSuggestionImageInline(admin.TabularInline):
    """Inline admin for product images."""
    model = ProductSuggestionImage
    extra = 0
    fields = ('image_preview', 'image')
    readonly_fields = ('image_preview',)

    @admin.display(description='Imagen')
    def image_preview(self, obj):
        """Display a thumbnail of the image."""
        if obj.image:
            return format_html(f'<img src="{obj.image.url}" style="width: 75px; height: auto;" />')
        return "-"


@admin.register(ProductSuggestion)
class ProductSuggestionAdmin(admin.ModelAdmin):
    """Admin configuration for ProductSuggestion model."""
    list_display = ('user', 'display_name', 'phone', 'display_images', 'description', 'created_formatted')
    list_display_links = ['user']
    list_per_page = 10
    inlines = [ProductSuggestionImageInline]
    fields = ['user', 'display_images', 'description', 'created_formatted']
    readonly_fields = ['created_formatted', 'display_images']
    save_on_top = True

    @admin.display(description='Nombre')
    def display_name(self, obj):
        """Display user's name, if exists."""
        first_name = obj.user.first_name if obj.user.first_name else ''
        last_name = obj.user.last_name if obj.user.last_name else ''
        return first_name + ' ' + last_name

    @admin.display(description='Creación')
    def created_formatted(self, obj):
        return obj.created.strftime("%d.%m.%Y %H:%M")

    @admin.display(description='Imágenes')
    def display_images(self, obj):
        """Display all related images in a list."""
        images = obj.images.all()
        if images.exists():
            return format_html(
                ''.join(
                    f"'<a href='{image.image.url}'><img src='{image.image.url}' style='width: 50px; height: auto; margin-right: 5px;' />"
                    for image in images
                )
            )
        return "No hay imágenes"
