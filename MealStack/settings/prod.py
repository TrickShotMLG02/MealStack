from .base import *

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mealstack',
        'USER': 'user',
        'PASSWORD': 'pass',
        'HOST': 'host',
        'PORT': '3306',
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

ALLOWED_HOSTS = []