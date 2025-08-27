from django.templatetags.static import static

from orders.models import OrderItem
from django.conf import settings

from django.utils.translation import gettext_lazy as _

from typing import Any


def get_context_menu(request) -> dict[str, Any]:
    """
    Constructs a context menu for site navigation based on user authentication status.
    Adds options for cart, likes, search, login/profile, and language selection.
    """
    menu_items = [
        {'title': "Buscar", 'url_name': 'product_search', 'url_icon': static('/products/images/svg/menu/search-1.svg')},
        {'title': "Likes", 'url_name': 'users:likes', 'url_icon': static('/products/images/svg/menu/heart-1.svg')},
        {'title': "Carrito", 'url_name': 'cart:cart_detail', 'url_icon': static('/products/images/svg/menu/cart.svg')},
    ]

    has_uncommented_items = False

    user_menu = {'title': _('Iniciar Sesión'),
                 'url_name': 'users:login',
                 'url_icon': static('products/images/svg/offcanvas/guest.png')}

    # Customize menu for authenticated users
    if request.user.is_authenticated:
        # Replace "Login" with "Profile" for logged-in users
        user_menu = {'title': _('Hola') + f', {request.user.first_name if request.user.first_name else request.user.username}',
                     'url_name': 'users:profile',
                     'url_icon': static('products/images/svg/offcanvas/user.png')}

        # Check if user has items they haven't commented on
        has_uncommented_items = OrderItem.objects.filter(
            order__user=request.user,
            order__paid_full=True,
            commented=False
        ).exists()

    return {
        'menu': menu_items,
        'user_menu': user_menu,
        'has_uncommented_items': has_uncommented_items,
        'languages': settings.LANGUAGES,
        'facebook_link_desktop': settings.FACEBOOK_LINK_DESKTOP,
        'facebook_link_mobile': settings.FACEBOOK_LINK_MOBILE,
        'instagram_link': settings.INSTAGRAM_LINK,
    }
