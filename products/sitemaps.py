from django.contrib.sitemaps import GenericSitemap
from .models import Product, Category, Tag, ThematicCategory

# Sitemap configurations for products, categories, tags, and thematic categories including update frequency and priority
products_info_dict = {
    "queryset": Product.published.all(),
}

categories_info_dict = {
    "queryset": Category.objects.all(),
}

tags_info_dict = {
    "queryset": Tag.objects.all(),
}

thematic_categories_info_dict = {
    "queryset": ThematicCategory.objects.all(),
}

sitemaps = {
    "products": GenericSitemap(products_info_dict, priority=0.9, changefreq='weekly'),
    "categories": GenericSitemap(categories_info_dict, priority=0.7, changefreq='monthly'),
    "tags": GenericSitemap(tags_info_dict, priority=0.5, changefreq='weekly'),
    "thematic_categories": GenericSitemap(thematic_categories_info_dict, priority=0.6, changefreq='weekly'),
}

