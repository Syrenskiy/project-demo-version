import requests
from django.conf import settings


def verify_turnstile(token: str, ip: str | None = None) -> bool:
    data = {
        "secret": settings.CLOUDFLARE_TURNSTILE_SECRET_KEY,
        "response": token
    }
    if ip:
        data["remoteip"] = ip

    response = requests.post(
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        data=data
    )

    result = response.json()
    return result.get("success", False)
