import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ENVIRONMENT = os.getenv("DJANGO_ENV", "develop")

if ENVIRONMENT == "production":
    from .settings.production import *
else:
    from .settings.development import *
