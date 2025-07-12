from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from accounts.models import MonthlyCenterReport
from decimal import Decimal
from datetime import datetime

from main.models import Enrollment
from accounts.models import CenterPayment

@receiver([post_save, post_delete], sender=Enrollment)
def update_monthly_stats(sender, instance, **kwargs):
    course = instance.course
    center = course.branch.edu_center
    applied = instance.applied_at
    year, month = applied.year, applied.month

    enrollments = Enrollment.objects.filter(
        course__branch__edu_center=center,
        applied_at__year=year,
        applied_at__month=month
    )

    total_apps = enrollments.count()
    total_payable = sum((e.course.price * Decimal('0.03')) for e in enrollments)

    MonthlyCenterReport.objects.update_or_create(
        edu_center=center,
        year=year,
        month=month,
        defaults={
            'total_applications': total_apps,
            'payable_amount': total_payable
        }
    )


@receiver(post_save, sender=CenterPayment)
def update_paid_in_report(sender, instance, **kwargs):
    today = datetime.today()
    year = today.year
    month = today.month

    report, _ = MonthlyCenterReport.objects.get_or_create(
        edu_center=instance.edu_center,
        year=year,
        month=month
    )
    report.paid_amount = instance.paid_amount
    report.save()
