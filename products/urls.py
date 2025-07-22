from django.urls import path
from django.views.decorators.cache import cache_page

from . import views

from django.utils.translation import gettext_lazy as _

# Define URL patterns for the products application with caching applied to some views.
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path(_('nosotros/'), cache_page(60 * 15)(views.AboutUsView.as_view()), name='about'),
    path(_('producto/<slug:category_slug>/<slug:product_slug>/comentario/'),
         views.CommentView.as_view(), name='product_comment'),
    path(_('producto/<slug:category_slug>/<slug:product_slug>/<slug:color_slug>/'),
         views.ProductDetailView.as_view(), name='product'),
    path(_('categoria/<slug:category_slug>/'), views.CategoryView.as_view(), name='category'),
    path(_('categoria-tematica/<slug:thematic_category_slug>/'),
         views.ThematicCategoryView.as_view(), name='thematic_category'),
    path(_('etiqueta/<slug:tag_slug>/'), views.TagView.as_view(), name='tag'),
    path(_('busqueda/'), views.product_search, name='product_search'),
    path('like/', views.LikeView.as_view(), name='like'),
    path(_('propuesta/'), views.ProductSuggestionCreateView.as_view(), name='product_suggestion'),
]
