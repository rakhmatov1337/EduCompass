# educompass/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# DRF va JWT-views importlari:
from rest_framework_simplejwt.views import (
    TokenObtainPairView,   # login uchun
    TokenRefreshView,      # token yangilash uchun
    TokenBlacklistView     # logout uchun (refresh-token blacklisting)
)
# Djoser-ning UserViewSet’ini import qilamiz:
from djoser.views import UserViewSet

# Siz oldin yozgan boshqa include’lar:
from main import urls as main_urls
from api import urls as api_urls
from accounts import urls as accounts_urls
from dashboard import urls as dashboard_urls
import debug_toolbar

# Swagger uchun (istenilsa):
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="EduCompass API",
        default_version='v1',
        description="EduCompass platformasi uchun avtomatik API hujjatlari",
        contact=openapi.Contact(email="support@educompas.uz"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(main_urls)),
    path('api/', include(api_urls)),
    path('accounts/', include(accounts_urls)),
    path('dashboard/', include(dashboard_urls)),
    path('auth/login/',  TokenObtainPairView.as_view(),   name='auth_login'),
    path('auth/refresh/', TokenRefreshView.as_view(),     name='token_refresh'),
    path('auth/logout/', TokenBlacklistView.as_view(),    name='auth_logout'),

    path('auth/register/',
         UserViewSet.as_view({'post': 'create'}),       name='auth_register'),
    path('auth/me/',
         UserViewSet.as_view({'get':  'current_user'}), name='auth_current_user'),
    path('swagger.json', schema_view.without_ui(
        cache_timeout=0), name='schema-json'),
    path('swagger/',     schema_view.with_ui('swagger',
         cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/',       schema_view.with_ui('redoc',
         cache_timeout=0), name='schema-redoc'),
]
if settings.DEBUG:
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
