from django.contrib.auth.models import Group, AbstractBaseUser
from users.tasks import send_registration_email

from typing import Any


def new_users_handler(backend, user: AbstractBaseUser, response, is_new: bool,
                      *args: Any, **kwargs: Any) -> None:
    """
    Handler for new users authenticated via social login.
    Adds new social-authenticated users to the "social" group and sends a welcome email.
    """
    if is_new:
        group = Group.objects.filter(name='social')
        if group.exists():
            user.groups.add(group.first())

        send_registration_email.delay(user.email)

