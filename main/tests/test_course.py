import pytest
from django.contrib.auth import get_user_model
from faker import Faker
from rest_framework import status
from rest_framework.test import APIClient

from main.models import Branch, Category, Day, EducationCenter, Level, Teacher

faker = Faker()


@pytest.mark.django_db
class TestCreateCourse:
    def test_if_user_is_anonymous_then_401(self):
        client = APIClient()

        # 1. Fake user va education center yaratamiz
        User = get_user_model()
        user = User.objects.create_user(
            username="testuser",
            password="Test1234!",
            full_name="Test User",
            role="EDU_CENTER",
        )

        edu_center = EducationCenter.objects.create(
            name=faker.company(),
            user=user,
            country="Uzbekistan",
            region="Tashkent",
            city="Tashkent",
        )

        # 2. Test uchun kerakli ma'lumotlarni yaratamiz
        branch = Branch.objects.create(
            name=faker.company(),
            edu_center=edu_center,
        )

        category = Category.objects.create(name=faker.word())
        level = Level.objects.create(name=faker.word())
        teacher = Teacher.objects.create(
            name=faker.name(), gender="MALE", branch=branch
        )
        day1 = Day.objects.create(name="MONDAY")
        day2 = Day.objects.create(name="WEDNESDAY")

        response = client.post(
            "/api/courses/",
            {
                "name": "Sample Course",
                "branch": branch.id,
                "category": category.id,
                "level": level.id,
                "teacher": teacher.id,
                "days": [day1.id, day2.id],
                "total_places": 20,
                "price": "300.00",
                "start_time": "10:00:00",
                "end_time": "12:00:00",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
