from django.contrib.auth.views import LogoutView, PasswordChangeView, PasswordChangeDoneView, PasswordResetView, \
    PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import path, reverse_lazy
from . import views

from django.utils.translation import gettext_lazy as _

from .views import PasswordResetUserView, PasswordResetConfirmUserView, PasswordChangeUserView, \
    PasswordChangeDoneUserView

# URL patterns for user authentication, profile management, and related views.


app_name = 'users'

urlpatterns = [
    # Login and logout
    path('login/', views.LoginUserView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),

    # Registration and profile
    path('register/', views.RegisterUserView.as_view(), name='register'),
    path('register-done/', views.RegisterDoneView.as_view(), name='register_done'),
    path(_('perfil/historial_de_compras/'), views.PurchaseHistoryView.as_view(), name='purchase_history'),
    path(_('comentarios/'), views.UsersCommentsView.as_view(), name='comments'),
    path(_('perfil/'), views.ProfileUserView.as_view(), name='profile'),

    # Password management
    path('password-change/', PasswordChangeUserView.as_view(), name='password_change'),
    path('password-change/done/', PasswordChangeDoneUserView.as_view(template_name='users/password_change_done.html'),
         name='password_change_done'),
    path('password-reset/', PasswordResetUserView.as_view(), name='password_reset'),
    path('password-reset/done/',
         PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', PasswordResetConfirmUserView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/',
         PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'),
         name='password_reset_complete'),

    # User's liked products
    path('likes/', views.UsersLikesView.as_view(), name='likes'),
]