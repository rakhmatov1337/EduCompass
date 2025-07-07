import os
import logging
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "educompass.settings")

app = Celery("educompass")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

logging.getLogger("celery.beat").info(
    f"Loaded beat_schedule: {app.conf.beat_schedule!r}")
