"""
ASGI config for MealStack project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Load settings from .env
import MealStack.settings.settings_selector  # noqa: F401

#os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MealStack.settings')

application = get_asgi_application()
