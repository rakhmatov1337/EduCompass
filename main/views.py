from django.shortcuts import get_object_or_404
from django.db.models import F

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema
from django.utils.decorators import method_decorator

from main.models import EduType, Category, Level, Day, Teacher, Course, Event
from main.models import Enrollment

from api.serializers import (
    EduTypeSerializer,
    CategorySerializer,
    LevelSerializer,
    DaySerializer,
    TeacherSerializer,
    CourseSerializer,
    EventSerializer
)
from accounts.serializers import EmptySerializer, MyCourseSerializer
from api.permissions import IsSuperUserOrReadOnly, IsEduCenterBranchOrReadOnly
from api.filters import CourseFilter, EventFilter
from api.paginations import DefaultPagination


# ─── EduType / Category / Level / Day ─────────────────────────────────────

@method_decorator(name='list',   decorator=swagger_auto_schema(operation_summary="List all education types", tags=["EduType"]))
@method_decorator(name='create', decorator=swagger_auto_schema(operation_summary="Create a new education type (Superuser only)", tags=["EduType"]))
class EduTypeViewSet(viewsets.ModelViewSet):
    queryset = EduType.objects.all()
    serializer_class = EduTypeSerializer
    permission_classes = [IsSuperUserOrReadOnly]


@method_decorator(name='list',   decorator=swagger_auto_schema(operation_summary="List all course categories", tags=["Category"]))
@method_decorator(name='create', decorator=swagger_auto_schema(operation_summary="Create a new category (Superuser only)", tags=["Category"]))
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsSuperUserOrReadOnly]


@method_decorator(name='list',   decorator=swagger_auto_schema(operation_summary="List all course levels", tags=["Level"]))
@method_decorator(name='create', decorator=swagger_auto_schema(operation_summary="Create a new course level (Superuser only)", tags=["Level"]))
class LevelViewSet(viewsets.ModelViewSet):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    permission_classes = [IsSuperUserOrReadOnly]


@method_decorator(name='list',   decorator=swagger_auto_schema(operation_summary="List all week days", tags=["Day"]))
@method_decorator(name='create', decorator=swagger_auto_schema(operation_summary="Add a new week day (Superuser only)", tags=["Day"]))
class DayViewSet(viewsets.ModelViewSet):
    queryset = Day.objects.all()
    serializer_class = DaySerializer
    permission_classes = [IsSuperUserOrReadOnly]


# ─── Teacher ────────────────────────────────────────────────────────────────

@method_decorator(name='list',     decorator=swagger_auto_schema(operation_summary="List all teachers", tags=["Teacher"]))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(operation_summary="Retrieve a specific teacher", tags=["Teacher"]))
class TeacherViewSet(viewsets.ModelViewSet):
    """
    SAFE_METHODS:  everyone (AllowAny).
    Non-safe:      EDU_CENTER or BRANCH only.
    """
    queryset = Teacher.objects.select_related('branch')
    serializer_class = TeacherSerializer
    permission_classes = [IsEduCenterBranchOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_authenticated:
            if user.role == 'EDU_CENTER':
                return qs.filter(branch__edu_center__user=user)
            if user.role == 'BRANCH':
                return qs.filter(branch__admins=user)
        # STUDENT / anon: see all
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        branch = serializer.validated_data['branch']
        if user.role == 'EDU_CENTER':
            if branch.edu_center.user != user:
                raise PermissionDenied(
                    "You may only add teachers to your own center’s branches.")
        else:  # BRANCH
            if user not in branch.admins.all():
                raise PermissionDenied(
                    "You may only add teachers to your own branch.")
        serializer.save()


# ─── Course ─────────────────────────────────────────────────────────────────

@method_decorator(name='list',           decorator=swagger_auto_schema(
    operation_summary="List all courses",
    operation_description="Retrieve all courses with optional filters, search, ordering.",
    tags=["Course"]
))
@method_decorator(name='retrieve',        decorator=swagger_auto_schema(operation_summary="Retrieve a specific course", tags=["Course"]))
@method_decorator(name='create',          decorator=swagger_auto_schema(operation_summary="Create a new course (EDU_CENTER or BRANCH only)", tags=["Course"]))
@method_decorator(name='update',          decorator=swagger_auto_schema(operation_summary="Update an existing course", tags=["Course"]))
@method_decorator(name='partial_update',  decorator=swagger_auto_schema(operation_summary="Partially update a course", tags=["Course"]))
@method_decorator(name='destroy',         decorator=swagger_auto_schema(operation_summary="Delete a course", tags=["Course"]))
class CourseViewSet(viewsets.ModelViewSet):
    """
    list/retrieve:    AllowAny
    create/update:    EDU_CENTER or BRANCH
    apply/my_courses: any Authenticated user
    """
    queryset = (
        Course.objects.filter(is_archived=False)
        .select_related('branch', 'branch__edu_center', 'teacher', 'category', 'level')
        .prefetch_related('days')
    )
    serializer_class = CourseSerializer
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = CourseFilter
    search_fields = ['name', 'branch__edu_center__name',
                     'teacher__name', 'category__name']
    ordering_fields = ['price', 'total_places', 'start_date']
    ordering = ['start_date']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        if self.action in ['apply', 'my_courses']:
            return [IsAuthenticated()]
        # create / update / delete
        return [IsAuthenticated(), IsEduCenterBranchOrReadOnly()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_authenticated:
            if user.role == 'EDU_CENTER':
                return qs.filter(branch__edu_center__user=user)
            if user.role == 'BRANCH':
                return qs.filter(branch__admins=user)
        # STUDENT / anon: see all courses
        return qs

    @action(detail=True, methods=['post'], serializer_class=EmptySerializer)
    def apply(self, request, pk=None):
        course = get_object_or_404(Course, pk=pk, is_archived=False)
        user = request.user
        if Enrollment.objects.filter(user=user, course=course).exists():
            return Response({"detail": "Already applied."}, status=status.HTTP_400_BAD_REQUEST)
        Enrollment.objects.create(user=user, course=course)
        course.booked_places = F('booked_places') + 1
        course.save(update_fields=['booked_places'])
        return Response({
            "detail":    "Applied successfully.",
            "course_id": course.id,
            "user_id":   user.id
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='my-courses', url_name='my_courses')
    def my_courses(self, request):
        qs = Enrollment.objects.filter(user=request.user)\
            .select_related('course__level')\
            .prefetch_related('course__days')
        ser = MyCourseSerializer(qs, many=True, context={'request': request})
        return Response(ser.data)


# ─── Event ──────────────────────────────────────────────────────────────────

@method_decorator(name='list',   decorator=swagger_auto_schema(
    operation_summary="List all events",
    operation_description="Retrieve all upcoming events.",
    tags=["Event"]
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(operation_summary="Retrieve a specific event", tags=["Event"]))
@method_decorator(name='create',   decorator=swagger_auto_schema(operation_summary="Create a new event (EDU_CENTER or BRANCH only)", tags=["Event"]))
@method_decorator(name='update',   decorator=swagger_auto_schema(operation_summary="Update an event", tags=["Event"]))
@method_decorator(name='destroy',  decorator=swagger_auto_schema(operation_summary="Delete an event", tags=["Event"]))
class EventViewSet(viewsets.ModelViewSet):
    """
    SAFE_METHODS: everyone
    Others:       EDU_CENTER or BRANCH
    """
    queryset = (
        Event.objects.filter(is_archived=False)
        .select_related('edu_center', 'branch')
        .prefetch_related('categories')
    )
    serializer_class = EventSerializer
    permission_classes = [IsEduCenterBranchOrReadOnly]
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = EventFilter
    search_fields = ['name', 'description']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_authenticated:
            if user.role == 'EDU_CENTER':
                return qs.filter(edu_center__user=user)
            if user.role == 'BRANCH':
                return qs.filter(branch__admins=user)
        # STUDENT / anon: see all
        return qs


# ─── Filter Schema endpoints ────────────────────────────────────────────────

class CourseFilterSchemaView(APIView):
    def get(self, request):
        return Response({
            'price_min':           '>= price',
            'price_max':           '<= price',
            'total_places_min':    '>= total places',
            'total_places_max':    '<= total places',
            'teacher_gender':      'male/female',
            'edu_center':          'center ID',
            'category':            'category ID',
        })


class EventFilterSchemaView(APIView):
    def get(self, request):
        return Response({
            'start_date':   'from YYYY-MM-DD',
            'end_date':     'to YYYY-MM-DD',
            'edu_center_id': 'comma–separated center IDs',
            'category':     'category filter',
        })
