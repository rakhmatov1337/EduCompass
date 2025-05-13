from django.urls import path
from rest_framework_nested import routers

from main.views import (
    EduTypeViewSet, CategoryViewSet,
    LevelViewSet, DayViewSet, TeacherViewSet, CourseViewSet)
from accounts.views import EduCenterViewSet, BranchViewSet, LikeViewSet, ViewViewSet, EduCenterCreateView


router = routers.DefaultRouter()

router.register('edu-types', EduTypeViewSet)
router.register('categories', CategoryViewSet)
router.register('levels', LevelViewSet)
router.register('days', DayViewSet)
router.register('teachers', TeacherViewSet, basename='teachers')
router.register('branches', BranchViewSet, basename='branches')
router.register('courses', CourseViewSet, basename='courses')
router.register('edu-centers', EduCenterViewSet, basename='edu-centers')

edu_center_router = routers.NestedDefaultRouter(
    router, r'edu-centers', lookup='edu_center')
edu_center_router.register('likes', LikeViewSet, basename='edu-center-likes')
edu_center_router.register('views', ViewViewSet, basename='edu-center-views')


urlpatterns = [
    path('edu-centers/create/', EduCenterCreateView.as_view(),
         name='edu-center-create')
] + router.urls + edu_center_router.urls
