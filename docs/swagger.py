from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="EduCompass API",
        default_version='v1',
        description="""
EduCompass API – Educational Center Management Platform

### Authentication
Use JWT authentication to register, login, and access protected endpoints. 

### Course Management
Courses can be created, updated, and deleted by authorized users (Branch or EduCenter).

### Teacher Management
Teachers are managed by branches. EduCenters can view all teachers across their branches.

### Filtering and Search
Courses support advanced filters (price, category, gender) and keyword search.

For full usage examples, contact the backend team or refer to each endpoint below.
        """,
        terms_of_service="https://educompass.uz/terms/",
        contact=openapi.Contact(email="support@educompass.uz"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
