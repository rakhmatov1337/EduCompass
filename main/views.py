from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from drf_yasg.utils import swagger_auto_schema
from django.utils.decorators import method_decorator

from api.serializers import *
from api.permissions import IsSuperUserOrReadOnly, IsEduCenterOrBranch
from api.filters import CourseFilter
from api.paginations import DefaultPagination
from .models import EduType, Category, Level


@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_summary="List all education types",
    tags=["EduType"]
))
@method_decorator(name='create', decorator=swagger_auto_schema(
    operation_summary="Create a new education type (Superuser only)",
    tags=["EduType"]
))
class EduTypeViewSet(ModelViewSet):
    queryset = EduType.objects.all()
    serializer_class = EduTypeSerializer
    permission_classes = [IsSuperUserOrReadOnly]

    def get_serializer_context(self):
        return {'request': self.request}


@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_summary="List all course categories",
    tags=["Category"]
))
@method_decorator(name='create', decorator=swagger_auto_schema(
    operation_summary="Create a new category (Superuser only)",
    tags=["Category"]
))
class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsSuperUserOrReadOnly]

    def get_serializer_context(self):
        return {'request': self.request}


@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_summary="List all course levels",
    tags=["Level"]
))
@method_decorator(name='create', decorator=swagger_auto_schema(
    operation_summary="Create a new course level (Superuser only)",
    tags=["Level"]
))
class LevelViewSet(ModelViewSet):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    permission_classes = [IsSuperUserOrReadOnly]

    def get_serializer_context(self):
        return {'request': self.request}


@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_summary="List all week days",
    tags=["Day"]
))
@method_decorator(name='create', decorator=swagger_auto_schema(
    operation_summary="Add a new week day (Superuser only)",
    tags=["Day"]
))
class DayViewSet(ModelViewSet):
    queryset = Day.objects.all()
    serializer_class = DaySerializer
    permission_classes = [IsSuperUserOrReadOnly]

    def get_serializer_context(self):
        return {'request': self.request}


@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_summary="List all teachers",
    tags=["Teacher"]
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_summary="Retrieve a specific teacher",
    tags=["Teacher"]
))
class TeacherViewSet(ReadOnlyModelViewSet):
    serializer_class = TeacherSerializer
    queryset = Teacher.objects.select_related('branch')

    def get_serializer_context(self):
        return {'request': self.request}


@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_summary="List all courses",
    operation_description="Retrieve all available courses with filters and search options."
                          " Supports filtering by category, level, teacher gender, price range, and more.",
    tags=["Course"]
))
@method_decorator(name='create', decorator=swagger_auto_schema(
    operation_summary="Create a new course",
    operation_description="Only EDU_CENTER or BRANCH users are allowed to create courses. BRANCH users will automatically be assigned to their branch.",
    tags=["Course"]
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_summary="Retrieve a specific course",
    tags=["Course"]
))
@method_decorator(name='update', decorator=swagger_auto_schema(
    operation_summary="Update an existing course",
    tags=["Course"]
))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(
    operation_summary="Partially update a course",
    tags=["Course"]
))
@method_decorator(name='destroy', decorator=swagger_auto_schema(
    operation_summary="Delete a course",
    tags=["Course"]
))
class CourseViewSet(ModelViewSet):
    serializer_class = CourseSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = CourseFilter
    search_fields = ['name', 'category__name', 'branch__edu_center__name']
    ordering_fields = ['price', 'total_places', 'start_date']
    pagination_class = DefaultPagination
    permission_classes = [IsEduCenterOrBranch]
    ordering = ['start_date']

    queryset = Course.objects.filter(is_archived=False) \
        .select_related('branch', 'branch__edu_center', 'teacher', 'category', 'level') \
        .prefetch_related('days')

    def get_serializer_context(self):
        return {'request': self.request}
