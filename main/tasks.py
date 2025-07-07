from celery import shared_task
from django.core import management
from django.utils import timezone
from io import StringIO
import logging

logger = logging.getLogger(__name__)


@shared_task
def export_monthly_applications_task():
    now = timezone.localtime()
    logger.info(f"[{now.isoformat()}] Running export_monthly_applications_task")
    out = StringIO()
    management.call_command("export_monthly_applications", stdout=out)
    result = out.getvalue().strip()
    # natijani ham log qilamiz
    logger.info(f"export_monthly_applications command output: {result}")
    return result  # natijani task return sifatida qaytaramiz



@shared_task
def ping():
    return "pong"
