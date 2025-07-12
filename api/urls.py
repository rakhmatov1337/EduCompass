from django.urls import path
from rest_framework_nested import routers
from rest_framework_simplejwt.views import (TokenBlacklistView,
                                            TokenObtainPairView,
                                            TokenRefreshView)

from accounts.views import (BranchViewSet, CurrentUserRetrieveUpdateView,
                            EduCenterCreateView, EduCenterViewSet, LikeViewSet,
                            RegisterView, ViewViewSet)
from main.views import (AppliedStudentViewSet, CategoryViewSet,
                        CourseFilterSchemaView, CourseViewSet, DayViewSet,
                        EduTypeViewSet, EventFilterSchemaView, EventViewSet,
                        LevelViewSet, TeacherViewSet, BannerViewSet, CenterPaymentViewSet,
                        MonthlyCenterReportViewSet, PaidAmountLogViewSet)
from quiz.views import (
    QuizFilterSchemaView,
    LevelProgressView, PackViewSet
)

router = routers.DefaultRouter()
router.register("edu-types", EduTypeViewSet)
router.register("categories", CategoryViewSet)
router.register("levels", LevelViewSet)
router.register("days", DayViewSet)
router.register("teachers", TeacherViewSet, basename="teachers")
router.register("branches", BranchViewSet, basename="branches")
router.register("courses", CourseViewSet, basename="courses")
router.register("edu-centers", EduCenterViewSet, basename="edu-centers")
router.register("events", EventViewSet, basename="event")
router.register("applied-students", AppliedStudentViewSet, basename="applied-students")
router.register(r"banners", BannerViewSet, basename="banner")

# accounts routers
router.register(
    r'center-payments',
    CenterPaymentViewSet,
    basename='center-payments'
)
router.register(r"monthly-reports", MonthlyCenterReportViewSet,
                basename="monthly-reports")
router.register(r"center-payments/paid-logs", PaidAmountLogViewSet,
                basename="paid-logs")

# quiz routers
router.register(r'levels/(?P<level_id>\d+)/packs', PackViewSet, basename='level-packs')


edu_center_router = routers.NestedSimpleRouter(
    router, r"edu-centers", lookup="edu_center"
)
edu_center_router.register("likes", LikeViewSet, basename="edu-center-likes")
edu_center_router.register("views", ViewViewSet, basename="edu-center-views")


urlpatterns = (
    [
        path(
            "edu-centers/create/",
            EduCenterCreateView.as_view(),
            name="edu-center-create",
        ),
        path(
            "courses/filters/",
            CourseFilterSchemaView.as_view(),
            name="course-filter-schema",
        ),
        path(
            "events/filters/",
            EventFilterSchemaView.as_view(),
            name="event-filter-schema",
        ),
        path('quizzes/filters/', QuizFilterSchemaView.as_view(), name='quiz-filter-schema'),
        path("auth/login/", TokenObtainPairView.as_view(), name="auth_login"),
        path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
        path("auth/logout/", TokenBlacklistView.as_view(), name="auth_logout"),
        path("auth/register/", RegisterView.as_view(), name="auth_register"),
        path(
            "auth/me/",
            CurrentUserRetrieveUpdateView.as_view(),
            name="auth_current_user",
        ),
        path("levels/<int:level_id>/progress/",
             LevelProgressView.as_view(),  name="level-progress"),
    ]
    + router.urls
    + edu_center_router.urls
)
