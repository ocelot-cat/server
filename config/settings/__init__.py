import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ENVIRONMENT = os.getenv("DJANGO_ENV", "development")

if ENVIRONMENT == "production":
    from .production import *
else:
    from .development import *
