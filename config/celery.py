import os
from celery import Celery
from celery.schedules import crontab

# from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

# test
# app.conf.beat_schedule = {
#     "create-daily-product-snapshots": {
#         "task": "products.tasks.create_daily_product_snapshots",
#         "schedule": 30.0,
#         "options": {"timezone": "Asia/Seoul"},
#     },
# }

app.conf.beat_schedule = {
    "create-daily-product-snapshots": {
        "task": "products.tasks.create_daily_product_snapshots",
        "schedule": crontab(hour=0, minute=0),
        "options": {"timezone": "Asia/Seoul"},
    },
}
