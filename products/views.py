import json
import logging
from math import ceil

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages import get_messages
from django.contrib.postgres.aggregates import StringAgg
from django.contrib.postgres.search import SearchVector
from django.core.cache import cache
from django.db.models.functions import Coalesce
from django.http import JsonResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.timezone import now
from django.views import View
from django.views.generic import ListView, DetailView, TemplateView, CreateView
from django.db.models import Count, Avg, Prefetch, Subquery, Value, TextField

from orders.models import OrderItem
from .forms import CommentForm, SearchForm, CartAddProductForm, ProductSuggestionForm
from .models import Product, Tag, Image, Color, ProductColor, ThematicCategory, ProductSuggestion, \
    ProductSuggestionImage, ProductQuantity, ProductSize
from .turnstile import verify_turnstile
from .utils import DataMixin, generate_cache_key, get_ru_suffix

from django.utils.translation import gettext_lazy as _, get_language

logger = logging.getLogger('django')


class HomeView(DataMixin, ListView):
    """Main product listing view for the home page."""
    template_name = 'products/index.html'
    context_object_name = 'products'
    title_page = _('Página principal')
    cat_selected = 0

    def get_queryset(self):
        """Fetch published products with related categories and translations, and calculate min price."""
        try:
            return (Product.published
                    .with_min_price()
                    .select_related('category')
                    .prefetch_related(
                        'translations',
                        'category__translations',
                        Prefetch('colors',
                            queryset=ProductColor.objects.prefetch_related('color__translations').order_by('id')
                        )
                    )
            )
        except Exception as e:
            logger.error(f"Error al obtener la lista de productos: {e}")
            return Product.objects.none()

    def get_context_data(self, **kwargs):
        """Add extra context including thematic categories."""
        context = super().get_context_data(**kwargs)
        active_thematic_categories = (
            ThematicCategory.objects.filter(valid_from__lte=now(), valid_to__gte=now())
                                    .filter(products__is_published=Product.Status.PUBLISHED)
                                    .prefetch_related('translations')
                                    .distinct()
        )
        context['thematic_categories'] = active_thematic_categories
        return context


class AboutUsView(DataMixin, TemplateView):
    """Static page view for the 'About Us' section."""
    template_name = 'products/about.html'
    title_page = _('Sobre Nosotros')


class Custom404View(DataMixin, TemplateView):
    """Custom 404 error view."""
    template_name = 'products/404.html'
    title_page = _('404 Página no encontrada')


class CategoryView(DataMixin, ListView):
    """View for displaying products filtered by category."""
    template_name = 'products/index.html'
    context_object_name = 'products'
    allow_empty = False

    def get_queryset(self):
        """Fetch products by the category slug with related data."""
        try:
            return (Product.published
                    .with_min_price()
                    .filter(category__translations__slug=self.kwargs['category_slug'])
                    .select_related('category')
                    .prefetch_related(
                        'translations',
                        'category__translations',
                        Prefetch('colors',
                                        queryset=ProductColor.objects.select_related('color')
                                        .prefetch_related('color__translations').order_by('id')
                        )
                    )
            )
        except Exception as e:
            logger.error(f"Error al filtrar productos por categoría: {e}")
            return Product.objects.none()

    def get_context_data(self, **kwargs):
        """Add extra context including selected category details."""
        context = super().get_context_data(**kwargs)
        cat = context['products'][0].category
        return self.get_mixin_context(context, title=cat.name, cat_selected=cat.pk)


class ThematicCategoryView(DataMixin, ListView):
    """View for displaying products filtered by thematic category."""
    template_name = 'products/index.html'
    context_object_name = 'products'
    allow_empty = False

    def get_queryset(self):
        """Fetch products associated with a specific thematic category slug."""
        try:
            return (Product.published.with_min_price()
                    .filter(thematic_categories__translations__slug=self.kwargs['thematic_category_slug'])
                    .select_related('category')
                    .prefetch_related(
                        'translations',
                        'colors__color'
                    )
            )
        except Exception as e:
            logger.error(f"Error al obtener la lista de categorías temáticas: {e}")
            return Product.objects.none()

    def get_context_data(self, **kwargs):
        """Add extra context including thematic category details."""
        context = super().get_context_data(**kwargs)
        thematic_category = ThematicCategory.objects.get(translations__slug=self.kwargs['thematic_category_slug'])
        return self.get_mixin_context(context, title=thematic_category.name)


class ProductDetailView(DataMixin, DetailView):
    """Detailed view for individual product pages."""
    template_name = 'products/product.html'
    slug_url_kwarg = 'product_slug'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        """Generate product detail page context, including related items and comments."""
        try:
            context = super().get_context_data(**kwargs)
            product = self.get_object()

            color_slug = self.kwargs.get('color_slug')
            color = self.get_color(color_slug)

            all_images = self.get_images(product, color)
            cart_product_form = CartAddProductForm(product=product, color=color)
            similar_products_urls = self.get_similar_products_urls(product)
            average_rating = self.get_average_rating(product)

            comments = self.get_comments(product)
            comments_per_page = 10
            total_comments = comments.count()
            total_pages = ceil(total_comments / comments_per_page)
            suffix = get_ru_suffix('comments', total_comments)

            need_to_show_product_quantity = self.show_product_quantity(product)
            absolute_url = self.build_absolute_url(product)
            return self.get_mixin_context(context, title=context['product'].name,
                                          comments=comments, form=CommentForm(), suffix=suffix,
                                          color=color, color_slug=color_slug, absolute_url=absolute_url,
                                          similar_products=similar_products_urls, all_images=all_images,
                                          cart_product_form=cart_product_form, total_pages=total_pages,
                                          average_rating=average_rating, total_comments=total_comments,
                                          need_to_show_product_quantity=need_to_show_product_quantity)
        except Product.DoesNotExist:
            logger.warning(f"Producto no encontrado: {self.kwargs.get(self.slug_url_kwarg)}")
            raise Http404(_("Producto no encontrado"))
        except Exception as e:
            logger.error(f"Error de visualización del producto: {e}")
            return {}

    def get_object(self, queryset=None):
        """Retrieve product instance and cache it to prevent redundant queries."""
        if not hasattr(self, '_product'):
            self._product = get_object_or_404(
                Product.published
                .with_min_price()
                .prefetch_related('colors__color__translations'),
                translations__slug=self.kwargs[self.slug_url_kwarg]
            )
        return self._product

    @staticmethod
    def get_color(color_slug):
        """Fetch color by slug."""
        return get_object_or_404(Color, translations__slug=color_slug)

    @staticmethod
    def get_images(product, color):
        """Retrieve product images for the specified color."""
        return Image.objects.filter(product_color__product=product, product_color__color=color)

    @staticmethod
    def get_similar_products_urls(product):
        """Fetch URLs for similar products by shared tags."""
        product_tags_ids = product.tags.values_list('id', flat=True)
        similar_products = (
            Product.published
            .with_min_price()
            .filter(tags__in=product_tags_ids)
            .exclude(id=product.id)
            .select_related('category')
            .prefetch_related(
                'category__translations',
                'translations',
                'colors__color__translations'
            )
            .annotate(same_tags=Count('tags'))
            .order_by('-same_tags')[:10]
        )

        similar_products_urls = []
        for similar_product in similar_products:
            first_color = similar_product.colors.all()[0]
            if first_color:
                url = reverse('product', kwargs={
                    'category_slug': similar_product.category.slug,
                    'product_slug': similar_product.slug,
                    'color_slug': first_color.color.slug
                })
                similar_products_urls.append((similar_product, url))

        return similar_products_urls

    @staticmethod
    def get_average_rating(product):
        """Calculate average rating of the product."""
        return product.comments.filter(active=True).aggregate(Avg('rating'))['rating__avg'] or 0

    @staticmethod
    def get_comments(product):
        """Retrieve active comments associated with the product."""
        return product.comments.filter(active=True).select_related('user')

    @staticmethod
    def show_product_quantity(product):
        """Determine whether to display product_quantity selection."""
        category = _("Recuerdos para Baby Shower")
        return not (product.category.name == category)

    def build_absolute_url(self, product):
        return self.request.build_absolute_uri(product.get_absolute_url())


class TagView(DataMixin, ListView):
    """View for displaying products filtered by tag."""
    template_name = 'products/index.html'
    context_object_name = 'products'
    allow_empty = False

    def get_queryset(self):
        """Fetch products associated with a specific tag slug."""
        try:
            return (Product.published.with_min_price()
                    .filter(tags__translations__slug=self.kwargs['tag_slug'])
                    .select_related('category')
                    .prefetch_related(
                        'category__translations',
                        'translations',
                        'colors__color'
                    )
            )
        except Exception as e:
            logger.error(f"Error al obtener la lista de etiquetas: {e}")
            return Product.objects.none()

    def get_context_data(self, **kwargs):
        """Add extra context including tag details."""
        context = super().get_context_data(**kwargs)
        tag = Tag.objects.get(translations__slug=self.kwargs['tag_slug'])
        return self.get_mixin_context(context, title=tag.name)


class CommentView(DataMixin, DetailView):
    """View to display and handle comments on a product."""
    model = Product
    template_name = 'products/comment.html'
    slug_url_kwarg = 'product_slug'

    def get_object(self, queryset=None):
        """Retrieve and cache the product object."""
        if not hasattr(self, '_product'):
            try:
                self._product = get_object_or_404(
                    Product.published.all(),
                    translations__slug=self.kwargs[self.slug_url_kwarg]
                )
            except Exception as e:
                logger.error(f"Error de visualización del producto al comentar: {e}")
                return Product.objects.none()
        return self._product

    def get_context_data(self, **kwargs):
        """Add context data for the comment form."""
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        category_slug = self.kwargs.get('category_slug')

        context.update({
            'title': _('Comentario de %(product_name)s') % {'product_name': product.name},
            'comments': product.comments.filter(active=True),
            'form': CommentForm(),
            'category_slug': category_slug,
        })
        return context

    def post(self, request, *args, **kwargs):
        """Handle comment form submission."""
        product = self.get_object()
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.product = product
            comment.user = request.user
            comment.save()
            try:
                items_commented = OrderItem.objects.filter(product=product,
                                                           order__user=request.user,
                                                           order__paid_full=True,
                                                           commented=False)
            except Exception as e:
                logger.error(f"Error al obtener la lista de productos para comentarlos: {e}")
                items_commented = OrderItem.objects.none()

            for item in items_commented:
                item.commented = True
                item.save()

            messages.success(request, _('Gracias por tu comentario! Será publicado tras la revisión del equipo'))

            return redirect(product.get_absolute_url())
        else:
            context = self.get_context_data(form=form)
            return self.render_to_response(context)


def product_search(request):
    """Handle product search functionality."""
    form = SearchForm()
    query = None
    results = []

    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']

            # Generate a unique cache key for the search query
            cache_key = generate_cache_key('search', query)
            results = cache.get(cache_key)
            if not results:
                try:
                    subresults = (
                        Product.published
                        .with_min_price()
                        .select_related('category')
                        .prefetch_related(
                            'translations',
                            'colors__color__translations',
                            'category__translations',
                            'tags__translations',
                            'thematic_categories__translations',
                        )
                        .annotate(
                            tags_text=Coalesce(
                                StringAgg('tags__translations__name', delimiter=' ',
                                          output_field=TextField()), Value('', output_field=TextField())
                            ),
                            thematic_text=Coalesce(
                                StringAgg('thematic_categories__translations__name', delimiter=' ',
                                          output_field=TextField()), Value('', output_field=TextField())
                            )
                        ).annotate(
                            search=SearchVector(
                                'translations__name',
                                'translations__description',
                                'tags_text',
                                'thematic_text',
                            )
                        )
                        .filter(search=query)
                    )

                    unique_results = {product.pk: product for product in subresults}
                    results = list(unique_results.values())

                    cache.set(cache_key, results, timeout=60 * 5)
                except Exception:
                    logger.error(f"Error al buscar productos a petición de '{query}'", exc_info=True)

    total_results = len(results) if results else 0
    suffix = get_ru_suffix('search', total_results)
    logger.info(f'Consulta de búsqueda: "{query}" por el usuario {request.user}, Resultados totales: {total_results}')

    return render(request, 'products/search.html', {
        'form': form, 'query': query, 'results': results,
        'suffix': suffix, 'total_results': total_results,
        'title': _('Búsqueda')
    })


class LikeView(LoginRequiredMixin, View):
    """View to handle liking or unliking a product by a logged-in user."""

    def post(self, request, *args, **kwargs):
        """Toggle like status for a product based on user action."""
        product_id = request.POST.get('id')
        action = request.POST.get('action')
        if product_id and action:
            try:
                product = Product.published.get(pk=product_id)
                # Add or remove like based on the action
                if action == 'like':
                    product.likes.add(request.user)
                else:
                    product.likes.remove(request.user)
                return JsonResponse({'status': 'ok'})
            except Product.DoesNotExist:
                pass
        return JsonResponse({'status': 'error'})


class UpdatePriceView(View):
    """View to handle price updates based on selected size or quantity."""

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            size_id = data.get('size_id')
            quantity_id = data.get('quantity_id')

            product = Product.objects.get(id=product_id)

            price = None
            if size_id:
                price = (ProductSize.objects
                         .filter(product=product, size_id=size_id).values_list('price', flat=True).first())
            if quantity_id:
                price = (ProductQuantity.objects
                         .filter(product=product, quantity_id=quantity_id).values_list('price', flat=True).first())

            if price is not None:
                return JsonResponse({'success': True, 'price': float(price)})

            return JsonResponse({'success': False, 'message': 'Invalid size or quantity.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})


class ProductSuggestionCreateView(LoginRequiredMixin, CreateView):
    """View for creating custom offers."""
    model = ProductSuggestion
    form_class = ProductSuggestionForm
    template_name = 'products/product_suggestion_create.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        """Checking Turnstile and assign the logged-in user to the suggestion before saving."""
        token = form.cleaned_data.get('cf_turnstile_response')
        if not verify_turnstile(token, self.request.META.get('REMOTE_ADDR')):
            form.add_error(None, _('La validación del captcha falló'))
            return self.form_invalid(form)

        form.instance.user = self.request.user
        messages.success(self.request, _('Su propuesta ha sido enviada con éxito!'))
        return super().form_valid(form)

    def get_form_kwargs(self):
        """Pass the user instance to the form for autofill purposes."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Add extra context including Title and Turnstile."""
        context = super().get_context_data(**kwargs)
        context['title'] = _("Propuesta")
        context['CLOUDFLARE_TURNSTILE_SITE_KEY'] = settings.CLOUDFLARE_TURNSTILE_SITE_KEY
        return context


class PrivacyPolicyView(DataMixin, TemplateView):
    """Static page view for the 'Privacy Policy' section."""
    template_name = 'privacy-policy.html'
    title_page = _('Política de Privacidad')


