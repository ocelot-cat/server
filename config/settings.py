# config/settings.py
import os
from pathlib import Path
from .base import (
    BASE_DIR,
    SECRET_KEY,
    INSTALLED_APPS,
    MIDDLEWARE,
    ROOT_URLCONF,
    TEMPLATES,
    WSGI_APPLICATION,
    AUTH_USER_MODEL,
    LANGUAGE_CODE,
    TIME_ZONE,
    USE_I18N,
    USE_TZ,
    STATIC_URL,
    MEDIA_URL,
    MEDIA_ROOT,
    DEFAULT_AUTO_FIELD,
    REST_FRAMEWORK,
    SIMPLE_JWT,
    CORS_ALLOW_HEADERS,
    AUTH_PASSWORD_VALIDATORS,
    SWAGGER_SETTINGS,
    CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND,
)

ENVIRONMENT = os.getenv("DJANGO_ENV", "development")

if ENVIRONMENT == "production":
    from .production import (
        DEBUG,
        ALLOWED_HOSTS,
        CORS_ALLOW_ALL_ORIGINS,
        CORS_ALLOWED_ORIGINS,
        CSRF_TRUSTED_ORIGINS,
        DATABASES,
        STATIC_ROOT,
        DEFAULT_FILE_STORAGE,
        GS_BUCKET_NAME,
        GS_PROJECT_ID,
        GS_CREDENTIALS,
        CLOUDFLARE_API_TOKEN,
        CLOUDFLARE_ACCOUNT_ID,
        CLOUDFLARE_IMAGES_URL,
        CLOUDFLARE_ACCOUNT_HASH,
    )
else:
    from .development import (
        DEBUG,
        ALLOWED_HOSTS,
        CORS_ALLOW_ALL_ORIGINS,
        CSRF_TRUSTED_ORIGINS,
        DATABASES,
    )
