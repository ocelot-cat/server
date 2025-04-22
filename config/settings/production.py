import os
import json
from google.oauth2 import service_account
from .base import *
from .base import BASE_DIR

IS_LOCAL = os.getenv("IS_LOCAL", "false").lower() == "true"
PGDATABASE = os.getenv("PGDATABASE")
PGUSER = os.getenv("PGUSER")
PGPASSWORD = os.getenv("PGPASSWORD")
PGHOST = os.getenv("PGHOST_PUBLIC" if IS_LOCAL else "PGHOST")
PGPORT = os.getenv("PGPORT_PUBLIC" if IS_LOCAL else "PGPORT")

# 필수 환경 변수 확인
missing_vars = []
if not PGDATABASE:
    missing_vars.append("PGDATABASE")
if not PGUSER:
    missing_vars.append("PGUSER")
if not PGPASSWORD:
    missing_vars.append("PGPASSWORD")
if not PGHOST:
    missing_vars.append("PGHOST")
if not PGPORT:
    missing_vars.append("PGPORT")

if missing_vars:
    raise ValueError(
        f"Missing required environment variables: {', '.join(missing_vars)}"
    )

print(f"IS_LOCAL: {IS_LOCAL}")
print(f"PGHOST: {PGHOST}")
print(f"PGPORT: {PGPORT}")
print(f"PGDATABASE: {PGDATABASE}")
print(f"PGUSER: {PGUSER}")
print(f"PGPASSWORD: {PGPASSWORD[:4]}...")

DEBUG = True
ALLOWED_HOSTS = ["ocleot.up.railway.app"]
CORS_ALLOW_ALL_ORIGINS = False
CSRF_TRUSTED_ORIGINS = ["https://ocleot.up.railway.app"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": PGDATABASE,
        "USER": PGUSER,
        "PASSWORD": PGPASSWORD,
        "HOST": PGHOST,
        "PORT": PGPORT,
    }
}

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
WHITENOISE_MANIFEST_STRICT = False

DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
GS_BUCKET_NAME = None
GS_PROJECT_ID = None
GS_CREDENTIALS = None

CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_IMAGES_URL = os.getenv("CLOUDFLARE_IMAGES_URL")
CLOUDFLARE_ACCOUNT_HASH = os.getenv("CLOUDFLARE_ACCOUNT_HASH")
