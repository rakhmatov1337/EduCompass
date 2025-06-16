import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from main.models import (
    EduType,
    Category,
    Level,
    Day,
    EducationCenter,
    Branch,
    Teacher,
    Course,
    Enrollment,
)


@pytest.mark.django_db
def test_enrollment_report_counts():
    client = APIClient()

    user = User.objects.create_user(
        username="edu",
        full_name="Edu Center",
        password="pass",
        role="EDU_CENTER",
    )
    client.force_authenticate(user=user)

    edu_type = EduType.objects.create(name="Type")
    category = Category.objects.create(name="Cat")
    level = Level.objects.create(name="Level")
    day = Day.objects.create(name=Day.DayChoices.MONDAY)

    center = EducationCenter.objects.create(
        name="Center",
        user=user,
        country="c",
        region="r",
        city="c",
    )
    center.edu_type.add(edu_type)

    branch = Branch.objects.create(name="B1", edu_center=center)
    teacher = Teacher.objects.create(name="T1", gender="MALE", branch=branch)
    def make_course(name_suffix):
        c = Course.objects.create(
            name=f"Course{name_suffix}",
            branch=branch,
            category=category,
            level=level,
            total_places=10,
            teacher=teacher,
            price=100,
            start_time="09:00",
            end_time="10:00",
        )
        c.days.add(day)
        return c

    now = timezone.now()
    Enrollment.objects.create(user=user, course=make_course("1"), applied_at=now - timezone.timedelta(days=3))
    Enrollment.objects.create(user=user, course=make_course("2"), applied_at=now - timezone.timedelta(days=20))
    Enrollment.objects.create(user=user, course=make_course("3"), applied_at=now - timezone.timedelta(days=200))

    url = reverse("enrollment-report")
    resp = client.get(url)

    assert resp.status_code == 200
    data = resp.json()
    assert data["weekly"] == 1
    assert data["monthly"] == 2
    assert data["yearly"] == 3

