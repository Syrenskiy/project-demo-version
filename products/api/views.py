import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status
from rest_framework.response import Response

from products.api.pagination import StandardPagination
from products.api.serializers import ProductSerializer, CategorySerializer, TagSerializer
from products.models import Product, Category, Tag

from typing import Any


logger = logging.getLogger('api')


class LoggedViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Base viewset that adds logging to standard list and retrieve actions.
    Logs request actions and handles exceptions by logging errors and returning a generic error response.
    """
    def list(self, request, *args: Any, **kwargs: Any) -> Response:
        logger.info(f"Solicitud de lista de {self.get_queryset().model.__name__}")
        try:
            response = super().list(request, *args, **kwargs)
            return response
        except Exception as e:
            logger.error(f"Error al obtener la lista de {self.get_queryset().model.__name__}: {e}")
            return Response({"error": f"Error del servidor al solicitar {self.get_queryset().model.__name__.lower()}s"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args: Any, **kwargs: Any) -> Response:
        logger.info(f"Solicitud para obtener {self.get_queryset().model.__name__} con id {kwargs['pk']}")
        try:
            response = super().retrieve(request, *args, **kwargs)
            return response
        except Exception as e:
            logger.error(f"Error al obtener {self.get_queryset().model.__name__} con id {kwargs['pk']}: {e}")
            return Response({"error": f"Error del servidor al obtener {self.get_queryset().model.__name__.lower()}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductViewSet(LoggedViewSet):
    """
    ViewSet for handling product data with logging, pagination, and filtering.
    Filters products by category, tags, colors, and price, with optional ordering by price or likes.
    """
    queryset = (Product.published
                .with_min_price()
                .select_related('category')
                .prefetch_related(
                    'tags',
                    'colors__color',
                    'size',
                    'quantity',
                    'comments',
    ))
    serializer_class = ProductSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['category', 'tags']
    ordering_fields = ['likes_count', 'min_price', 'size_prices', 'quantity_prices']


class CategoryViewSet(LoggedViewSet):
    """ViewSet for handling category data with logging and pagination."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = StandardPagination


class TagViewSet(LoggedViewSet):
    """ViewSet for handling tag data with logging and pagination."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = StandardPagination

