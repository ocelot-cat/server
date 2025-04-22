import os
from .base import { BASE_DIR,SECRET_KEY,INSTALLED_APPS,MIDDLEWARE,STATICFILES_STORAGE,ROOT_URLCONF,TEMPLATES,WSGI_APPLICATION,AUTH_USER_MODEL,LANGUAGE_CODE,TIME_ZONE,USE_I18N,USE_TZ,STATIC_URL,MEDIA_URL,MEDIA_ROOT,DEFAULT_AUTO_FIELD,REST_FRAMEWORK,SIMPLE_JWT,CORS_ALLOW_HEADERS,AUTH_PASSWORD_VALIDATORS,SWAGGER_SETTINGS,CELERY_BROKER_URL,CELERY_RESULT_BACKEND}
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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("PGDATABASE"),
        "USER": os.getenv("PGUSER"),
        "PASSWORD": os.getenv("PGPASSWORD"),
        "HOST": os.getenv("PGHOST"),
        "PORT": os.getenv("PGPORT"),
    }
}


STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
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


CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_IMAGES_URL = os.getenv("CLOUDFLARE_IMAGES_URL")
CLOUDFLARE_ACCOUNT_HASH = os.getenv("CLOUDFLARE_ACCOUNT_HASH")
