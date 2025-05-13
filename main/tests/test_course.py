import pytest
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestCreateCourse:
    def test_if_user_is_anonymous_then_401(self):
        client = APIClient()
        response = client.post('/api/courses/', {
            "name": "Sample Course",
            "total_places": 20,
            "price": "300.00"
        }) 

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
