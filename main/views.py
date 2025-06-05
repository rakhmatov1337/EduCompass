from accounts.serializers import MyCourseSerializer
from .models import Course
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework import viewsets, status
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema
from django.utils.decorators import method_decorator

from accounts.serializers import EmptySerializer
from api.serializers import *
from api.permissions import IsSuperUserOrReadOnly, IsEduCenterOrBranch
from api.filters import CourseFilter, EventFilter
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
class CourseViewSet(viewsets.ModelViewSet):
    queryset = (
        Course.objects
        .filter(is_archived=False)
        .select_related('branch', 'branch__edu_center', 'teacher', 'category', 'level')
        .prefetch_related('days')
    )
    serializer_class = CourseSerializer

    # CRUD uchun permission: markaz va filial adminlari
    permission_classes = [IsEduCenterOrBranch]

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = CourseFilter
    search_fields = ['name', 'branch__edu_center__name',
                     'teacher__name', 'category__name']
    ordering_fields = ['price', 'total_places', 'start_date']
    ordering = ['start_date']
    pagination_class = DefaultPagination

    def get_serializer_context(self):
        return {'request': self.request}

    def get_permissions(self):
        """
        Agar action 'apply' yoki 'my_courses' bo'lsa → IsAuthenticated,
        aks holda → IsEduCenterOrBranch
        """
        if self.action in ['apply', 'my_courses']:
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        serializer_class=EmptySerializer,
        url_path='apply',
        url_name='apply'
    )
    def apply(self, request, pk=None):
        course = get_object_or_404(Course, pk=pk, is_archived=False)
        user = request.user

        if Enrollment.objects.filter(user=user, course=course).exists():
            return Response(
                {"detail": "Siz allaqachon ushbu kursga yozilgansiz."},
                status=status.HTTP_400_BAD_REQUEST
            )

        Enrollment.objects.create(user=user, course=course)

        course.booked_places = F('booked_places') + 1
        course.save(update_fields=['booked_places'])

        return Response(
            {
                "detail": "Kursga muvoffaqiyatli ro‘yxatdan oʻtildi.",
                "course_id": course.id,
                "user_id":   user.id
            },
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='my-courses',
        url_name='my_courses'
    )
    def my_courses(self, request):
        enrollments = (
            Enrollment.objects
            .filter(user=request.user)
            .select_related('course__level')
            .prefetch_related('course__days')
        )
        serializer = MyCourseSerializer(
            enrollments,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


class CourseFilterSchemaView(APIView):
    def get(self, request):
        filters = {
            'price_min': 'Narxdan katta yoki teng',
            'price_max': 'Narxdan kichik yoki teng',
            'total_places_min': 'Joylar soni kamida',
            'total_places_max': 'Joylar soni eng ko‘pi',
            'teacher_gender': 'O‘qituvchi jinsi (male/female)',
            'edu_center': 'Ta’lim markazi ID',
            'edu_center_name': 'Ta’lim markazi nomi',
            'category': 'Kurs kategoriyasi ID',
        }
        return Response(filters)


class EventViewSet(ReadOnlyModelViewSet):
    queryset = Event.objects.filter(is_archived=False) \
        .select_related('edu_center', 'branch') \
        .prefetch_related('categories')

    serializer_class = EventSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = EventFilter
    search_fields = ['name', 'description']
    pagination_class = DefaultPagination


class EventFilterSchemaView(APIView):
    def get(self, request):
        filters = {
            'start_date': 'Boshlanish sanasi (dan) – YYYY-MM-DD',
            'end_date': 'Tugash sanasi (gacha) – YYYY-MM-DD',
            'edu_center_id': 'Taʼlim markazlari IDlari (vergul bilan ajratilgan: 1,3,7)',
            'category': "Kategoriya bo'yicha saralash!"
        }
        return Response(filters)
