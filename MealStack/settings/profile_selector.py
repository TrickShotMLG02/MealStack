import os
from dotenv import load_dotenv

# Load .env from project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Determine environment
ENV = os.getenv("ENVIRONMENT", "dev")  # default to dev

if ENV == "dev":
    SETTINGS_MODULE = "MealStack.settings.dev"
elif ENV == "prod":
    SETTINGS_MODULE = "MealStack.settings.prod"
else:
    raise ValueError(f"Unknown ENVIRONMENT: {ENV}")

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", SETTINGS_MODULE)


def apply_env_overrides():
    """
    Apply environment variable overrides on top of the loaded profile settings.
    Should be called after Django has imported settings.
    """
    from django.conf import settings

    # DEBUG override
    debug_env = os.getenv("DEBUG")
    if debug_env:
        settings.DEBUG = debug_env.lower() in ("true", "1", "yes")

    # SECRET_KEY override
    secret_key_env = os.getenv("SECRET_KEY")
    if secret_key_env:
        settings.SECRET_KEY = secret_key_env

    # ALLOWED_HOSTS override
    allowed_hosts_env = os.getenv("ALLOWED_HOSTS")
    if allowed_hosts_env:
        settings.ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(",") if host.strip()]

    # ALLOWED_HOSTS override
    csrf_trusted_origins_env = os.getenv("CSRF_TRUSTED_ORIGINS")
    if csrf_trusted_origins_env:
        settings.CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_trusted_origins_env.split(",") if origin.strip()]

    # DATABASE overrides
    db_engine_env = os.getenv("DB_ENGINE")
    if db_engine_env:
        if db_engine_env == "sqlite":
            settings.DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": os.getenv("DB_NAME", settings.BASE_DIR / "db.sqlite3"),
                }
            }
        elif db_engine_env == "mysql":
            settings.DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.mysql",
                    "NAME": os.getenv("DB_NAME_MYSQL", "mealstack"),
                    "USER": os.getenv("DB_USER", "root"),
                    "PASSWORD": os.getenv("DB_PASSWORD", ""),
                    "HOST": os.getenv("DB_HOST", "127.0.0.1"),
                    "PORT": os.getenv("DB_PORT", "3306"),
                    "OPTIONS": {
                        "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
                    },
                }
            }
        else:
            raise ValueError(f"Unknown DB_ENGINE: {db_engine_env}")

    # OIDC override
    oidc_enabled_env = os.getenv("OIDC_ENABLED")
    if oidc_enabled_env:
        settings.OIDC_ENABLED = oidc_enabled_env.lower() in ("true", "1", "yes")

    # Default auth override
    oidc_allow_local_login_env = os.getenv("OIDC_ALLOW_LOCAL_LOGIN")
    if oidc_allow_local_login_env:
        settings.OIDC_ALLOW_LOCAL_LOGIN = oidc_allow_local_login_env.lower() in ("true", "1", "yes")

    if not settings.OIDC_ENABLED or settings.OIDC_ALLOW_LOCAL_LOGIN:
        settings.AUTHENTICATION_BACKENDS.append(
            "django.contrib.auth.backends.ModelBackend"
        )

    if settings.OIDC_ENABLED:
        settings.AUTHENTICATION_BACKENDS.append(
            "apps.common.backend.auth_backends.OIDCAuthBackend"
        )

        settings.OIDC_RP_CLIENT_ID = os.getenv("OIDC_CLIENT_ID")
        settings.OIDC_RP_CLIENT_SECRET = os.getenv("OIDC_CLIENT_SECRET")

        settings.OIDC_OP_AUTHORIZATION_ENDPOINT = os.getenv("OIDC_AUTHORIZATION_ENDPOINT")
        settings.OIDC_OP_TOKEN_ENDPOINT = os.getenv("OIDC_TOKEN_ENDPOINT")
        settings.OIDC_OP_USER_ENDPOINT = os.getenv("OIDC_USERINFO_ENDPOINT")
        settings.OIDC_OP_JWKS_ENDPOINT = os.getenv("OIDC_JWKS_ENDPOINT")

        settings.OIDC_RP_SIGN_ALGO = os.getenv("OIDC_RP_SIGN_ALGO")
        settings.OIDC_OP_ISSUER = os.getenv("OIDC_ISSUER")

        settings.OIDC_RP_SCOPES = os.getenv(
            "OIDC_SCOPES", "openid email profile"
        )

        settings.LOGIN_REDIRECT_URL = "/admin/"

    # Timezone Override
    tz_env = os.getenv("TIME_ZONE")
    if tz_env:
        settings.TIME_ZONE = tz_env

    # Default Language
    lang_env = os.getenv("DEFAULT_LANGUAGE")
    if lang_env:
        settings.LANGUAGE_CODE = lang_env


# Call it immediately to apply overrides
apply_env_overrides()