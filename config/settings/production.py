import os
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
from decouple import config
import json
from google.oauth2 import service_account

DEBUG = False
ALLOWED_HOSTS = [
    "ocleot.up.railway.app",
]
CORS_ALLOW_ALL_ORIGINS = False
CSRF_TRUSTED_ORIGINS = [
    "https://ocleot.up.railway.app",
]

ROOT_URLCONF = "config.urls"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("PGDATABASE"),
        "USER": config("PGUSER"),
        "PASSWORD": config("PGPASSWORD"),
        "HOST": config("PGHOST"),
        "PORT": config("PGPORT"),
    }
}

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
GS_BUCKET_NAME = config("GS_BUCKET_NAME")
GS_PROJECT_ID = config("GS_PROJECT_ID")
GS_CREDENTIALS = service_account.Credentials.from_service_account_info(
    json.loads(config("GOOGLE_CREDENTIALS"))
)

CLOUDFLARE_API_TOKEN = config("CLOUDFLARE_API_TOKEN")
CLOUDFLARE_ACCOUNT_ID = config("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_IMAGES_URL = config("CLOUDFLARE_IMAGES_URL")
CLOUDFLARE_ACCOUNT_HASH = config("CLOUDFLARE_ACCOUNT_HASH")
