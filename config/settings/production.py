import os
from .base import *
from .base import BASE_DIR
from decouple import config
import json
from google.oauth2 import service_account

ROOT_URLCONF = "config.urls"
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

# STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
GS_BUCKET_NAME = "django-ocelot"
GS_PROJECT_ID = "django-ocelot"

google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if google_credentials_path and os.path.exists(google_credentials_path):
    try:
        with open(google_credentials_path, "r") as f:
            google_credentials = json.load(f)
        GS_CREDENTIALS = service_account.Credentials.from_service_account_info(
            google_credentials
        )
    except json.JSONDecodeError as e:
        print(f"Error decoding Google Cloud credentials: {e}")
        GS_CREDENTIALS = None
else:
    print("GOOGLE_APPLICATION_CREDENTIALS not set or file not found")
    GS_CREDENTIALS = None


CLOUDFLARE_API_TOKEN = config("CLOUDFLARE_API_TOKEN")
CLOUDFLARE_ACCOUNT_ID = config("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_IMAGES_URL = config("CLOUDFLARE_IMAGES_URL")
CLOUDFLARE_ACCOUNT_HASH = config("CLOUDFLARE_ACCOUNT_HASH")
