import os
from .base import *
from .base import BASE_DIR, ROOT_URLCONF
from decouple import config
import json
from google.oauth2 import service_account
import logging

logger = logging.getLogger(__name__)
logger.info(f"ROOT_URLCONF in production.py: {ROOT_URLCONF}")
logger.info(f"DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}")


DEBUG = False
ALLOWED_HOSTS = [
    "ocleot.up.railway.app",
]
CORS_ALLOW_ALL_ORIGINS = False
CSRF_TRUSTED_ORIGINS = [
    "https://ocleot.up.railway.app",
]

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
