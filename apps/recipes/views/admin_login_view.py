from urllib.parse import urlencode

from django.shortcuts import redirect
from django.urls import reverse


def admin_login_redirect(request):
    """Use the regular account login page for admin authentication."""
    next_url = request.GET.get("next") or "/admin/"
    login_url = reverse("users:login")
    return redirect(f"{login_url}?{urlencode({'next': next_url})}")
