from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import AbstractBaseUser

from typing import Any


class EmailAuthBackend(BaseBackend):
    """Custom authentication backend allowing users to log in with their email and password."""
    def authenticate(self, request, username: str | None = None, password: str | None = None,
                     **kwargs: Any) -> AbstractBaseUser | None:
        """Authenticate the user based on email and password."""
        user_model = get_user_model()
        try:
            # The 'username' parameter is used as an email here
            user = user_model.objects.get(email=username)
            if user.check_password(password):
                return user
            return None
        except (user_model.DoesNotExist, user_model.MultipleObjectsReturned):
            return None

    def get_user(self, user_id: int) -> AbstractBaseUser | None:
        """Retrieve a user instance by their ID."""
        user_model = get_user_model()
        try:
            return user_model.objects.get(pk=user_id)
        except user_model.DoesNotExist:
            return None
