import os

from django.core.exceptions import ImproperlyConfigured

from .base import *


def required_env(name):
    value = os.getenv(name)
    if not value:
        raise ImproperlyConfigured(f"{name} must be set in production.")
    return value

DEBUG = False

SECRET_KEY = required_env("SECRET_KEY")

if os.getenv("DB_ENGINE") == "sqlite":
    DATABASES = {}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': required_env("DB_NAME_MYSQL"),
            'USER': required_env("DB_USER"),
            'PASSWORD': required_env("DB_PASSWORD"),
            'HOST': required_env("DB_HOST"),
            'PORT': os.getenv("DB_PORT", "3306"),
            "OPTIONS": {
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }

ALLOWED_HOSTS = []
