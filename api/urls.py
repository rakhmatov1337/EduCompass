# api/urls.py

from django.urls import path
from djoser.views import UserViewSet
from rest_framework_nested import routers
from rest_framework_simplejwt.views import (TokenBlacklistView,
                                            TokenObtainPairView,
                                            TokenRefreshView)

from accounts.views import (BranchViewSet, CurrentUserRetrieveUpdateView,
                            EduCenterCreateView, EduCenterViewSet, LikeViewSet,
                            MyCoursesView, RegisterView, ViewViewSet)
from main.views import (
    AppliedStudentViewSet,
    CategoryViewSet,
    CourseFilterSchemaView,
    CourseViewSet,
    DayViewSet,
    EduTypeViewSet,
    EnrollmentReportView,
    EventFilterSchemaView,
    EventViewSet,
    LevelViewSet,
    TeacherViewSet,
)
from quiz.views import (
    QuizViewSet, QuestionViewSet, AnswerViewSet,
    UserQuizResultViewSet, UserLevelProgressViewSet, QuizFilterSchemaView
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

# quiz routers

router.register(r'quizzes', QuizViewSet, basename='quiz')
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'answers', AnswerViewSet, basename='answer')
router.register(r'results', UserQuizResultViewSet, basename='results')
router.register(r'progress', UserLevelProgressViewSet, basename='progress')

edu_center_router = routers.NestedDefaultRouter(
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
        path(
            "reports/enrollments/",
            EnrollmentReportView.as_view(),
            name="enrollment-report",
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
    ]
    + router.urls
    + edu_center_router.urls
)
