"""
WSGI config for MealStack project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Load settings from .env
import MealStack.settings.settings_selector  # noqa: F401

#os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MealStack.settings')

application = get_wsgi_application()
