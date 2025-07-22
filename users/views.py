import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, TemplateView, ListView

from products.models import Product
from products.turnstile import verify_turnstile
from products.utils import DataMixin
from users.forms import LoginUserForm, RegisterUserForm, ProfileUserForm, PasswordResetUserForm, SetPasswordUserForm, \
    PasswordChangeUserForm
from users.tasks import send_registration_email

from django.utils.translation import gettext_lazy as _

logger = logging.getLogger('django')


class LoginUserView(LoginView):
    """Custom login view that logs successful and failed login attempts."""
    form_class = LoginUserForm
    template_name = 'users/login.html'
    extra_context = {'title': _('Iniciar sesión')}

    def form_valid(self, form):
        """Checking Turnstile and log successful login attempt."""
        token = form.cleaned_data.get('cf_turnstile_response')
        if not verify_turnstile(token, self.request.META.get('REMOTE_ADDR')):
            form.add_error(None, _('La validación del captcha falló'))
            return self.form_invalid(form)

        logger.info(f"Usuario {form.cleaned_data['username']} ha iniciado sesión correctamente.")
        return super().form_valid(form)

    def form_invalid(self, form):
        """Log failed login attempt."""
        try:
            username = form.cleaned_data['username']
            logger.warning(f"Intento de inicio de sesión fallido para usuario {username}.")
        except KeyError as e:
            logger.warning(f"Intento de inicio de sesión fallido, usuario incorrecto: {e}")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        """Add extra context Turnstile."""
        context = super().get_context_data(**kwargs)
        context['CLOUDFLARE_TURNSTILE_SITE_KEY'] = settings.CLOUDFLARE_TURNSTILE_SITE_KEY
        return context


class RegisterUserView(CreateView):
    """User registration view that sends a welcome email upon successful registration."""
    form_class = RegisterUserForm
    template_name = 'users/register.html'
    extra_context = {'title': _('Registrarse')}
    success_url = reverse_lazy('users:register_done')

    def form_valid(self, form):
        """Checking Turnstile, log the new user registration and send a welcome email asynchronously."""
        token = form.cleaned_data.get('cf_turnstile_response')
        if not verify_turnstile(token, self.request.META.get('REMOTE_ADDR')):
            form.add_error(None, _('La validación del captcha falló'))
            return self.form_invalid(form)

        user_email = form.instance.email
        logger.info(f"Nuevo usuario registrado con correo electrónico: {user_email}")
        try:
            send_registration_email.delay(user_email)  # Celery for asynchronous email sending
        except Exception as e:
            logger.error(f"Error al enviar correo de registro para {user_email}: {e}")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Add extra context Turnstile."""
        context = super().get_context_data(**kwargs)
        context['CLOUDFLARE_TURNSTILE_SITE_KEY'] = settings.CLOUDFLARE_TURNSTILE_SITE_KEY
        return context


class RegisterDoneView(TemplateView):
    """View displayed upon successful user registration."""
    template_name = 'users/register_done.html'
    extra_context = {'title': _('Bienvenido!')}


class PasswordResetUserView(PasswordResetView):
    """Custom password reset view with logging for successful and failed attempts."""
    form_class = PasswordResetUserForm
    template_name = 'users/password_reset_form.html'
    email_template_name = 'users/password_reset_email.html'
    success_url = reverse_lazy('users:password_reset_done')
    extra_context = {'title': _('Recuperación de contraseña')}

    def form_valid(self, form):
        """Log successful password reset attempt."""
        logger.info(
            f"Solicitud de restablecimiento de contraseña enviada correctamente para el correo {form.cleaned_data['email']}.")
        return super().form_valid(form)

    def form_invalid(self, form):
        """Log failed password reset attempt."""
        logger.warning(
            f"Fallo en la solicitud de restablecimiento de contraseña para el correo {form.cleaned_data['email']}.")
        return super().form_invalid(form)


class PasswordResetConfirmUserView(PasswordResetConfirmView):
    """Custom view for setting a new password."""
    form_class = SetPasswordUserForm
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')

    def form_valid(self, form):
        """Log successful password reset."""
        logger.info(f"El usuario ha cambiado su contraseña correctamente.")
        return super().form_valid(form)

    def form_invalid(self, form):
        """Log failed password reset."""
        logger.warning(f"Error en el cambio de contraseña para el usuario.")
        return super().form_invalid(form)


class PasswordChangeUserView(PasswordChangeView):
    form_class = PasswordChangeUserForm
    template_name = "users/password_change_form.html"
    success_url = reverse_lazy("users:password_change_done")
    extra_context = {'title': _('Cambio de contraseña')}


class PasswordChangeDoneUserView(TemplateView):
    """View displayed upon successful user registration."""
    template_name = 'users/password_change_done.html'
    extra_context = {'title': _('La contraseña se cambió correctamente!')}


class ProfileUserView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """View for updating the logged-in user's profile."""
    model = get_user_model()
    form_class = ProfileUserForm
    template_name = 'users/profile.html'
    success_message = _('Tu perfil ha sido actualizado exitosamente!')
    extra_context = {
        'title': _('Perfil'),
    }

    def get_success_url(self):
        """Redirect to profile page upon successful update."""
        return reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        """Return the logged-in user as the object for the view."""
        return self.request.user

    def form_invalid(self, form):
        """Display an error message if the form submission fails."""
        messages.error(self.request, _('Se produjo un error al actualizar el perfil.'))
        return super().form_invalid(form)


class PurchaseHistoryView(LoginRequiredMixin, DataMixin, ListView):
    """View displaying the purchase history of the logged-in user."""
    template_name = 'users/purchase_history.html'
    context_object_name = 'orders'
    title_page = _('Mis Pedidos')
    extra_context = {'delivery': _('A Domicilio')}
    paginate_by = 5

    def get_queryset(self):
        """Retrieve the logged-in user's paid orders along with related data."""
        user = self.request.user
        logger.info(f"El usuario {user.username} accedió a su historial de compras.")
        try:
            return (user.orders.filter(paid=True)
                    .prefetch_related(
                        'items',
                        'coupon',
                        'delivery__translations',
                        'items__product__translations',
                        'items__product__category__translations',
                        'items__product__colors__color__translations'
                    )
            )
        except Exception as e:
            logger.error(f"Error al obtener historial de compras para {user.username}: {e}")
            return []


class UsersLikesView(LoginRequiredMixin, ListView):
    """View displaying products liked by the logged-in user."""
    template_name = 'users/likes.html'
    context_object_name = 'products'
    extra_context = {'title': _('Mis Favoritos')}

    def get_queryset(self):
        """Retrieve the user's favorite products with related data."""
        user = self.request.user
        try:
            return (
                Product.published
                .with_min_price()
                .filter(likes=user)
                .select_related('category')
                .prefetch_related(
                    'colors__color__translations',
                    'translations',
                    'category__translations'
                )
            )
        except Exception as e:
            logger.error(f"Error al obtener productos favoritos para usuario {user.username}: {e}")
            return Product.objects.none()


class UsersCommentsView(LoginRequiredMixin, DataMixin, ListView):
    """View for displaying products the user can leave comments on."""
    model = get_user_model()
    template_name = 'users/comments.html'
    context_object_name = 'products'
    title_page = _('Dejar Comentarios')

    def get_queryset(self):
        """Retrieve products the user has purchased but has not yet commented on."""
        user = self.request.user
        try:
            return (Product.published.filter(
                items__order__user=user,
                items__order__paid_full=True,
                items__commented=False
            ).distinct()
                    .select_related('category')
                    .prefetch_related(
                        'category__translations',
                        'colors__color__translations',
                        'translations'
                    )
            )
        except Exception as e:
            logger.error(f"Error al obtener productos sin comentar para usuario {user.username}: {e}")
            return Product.objects.none()

    def get_object(self, queryset=None):
        """Return the user as the object for this view."""
        return get_object_or_404(self.model, pk=self.request.user.pk)
