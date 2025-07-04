# educompass/urls.py

import debug_toolbar
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from accounts import urls as accounts_urls
from api import urls as api_urls
from dashboard import urls as dashboard_urls
from main import urls as main_urls
from quiz import urls as quiz_urls

schema_view = get_schema_view(
    openapi.Info(
        title="EduCompass API",
        default_version="v1",
        description="EduCompass platformasi uchun avtomatik API hujjatlari",
        contact=openapi.Contact(email="support@educompas.uz"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(main_urls)),
    path("api/", include(api_urls)),
    path("accounts/", include(accounts_urls)),
    path("dashboard/", include(dashboard_urls)),
    path("quiz/", include(quiz_urls)),
    path("swagger.json", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
if settings.DEBUG:
    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
