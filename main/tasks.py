from celery import shared_task
from django.core import management
from django.utils import timezone


@shared_task
def export_monthly_applications_task():
    now = timezone.localtime()
    print(f"[{now.isoformat()}] Running export_monthly_applications_task")
    management.call_command("export_monthly_applications")


@shared_task
def ping():
    return "pong"
