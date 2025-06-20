from datetime import timedelta
from django.db.models import F
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import EmptySerializer, MyCourseSerializer
from api.permissions import IsSuperUserOrReadOnly
from api.filters import CourseFilter, EventFilter
from api.paginations import DefaultPagination
from api.permissions import IsEduCenterBranchOrReadOnly, IsSuperUserOrReadOnly
from api.serializers import (AppliedStudentSerializer, CategorySerializer,
                             CourseSerializer, DaySerializer,
                             EduTypeSerializer, EventSerializer,
                             LevelSerializer, TeacherSerializer, UnitSerializer, QuizTypeSerializer,
                             QuizSerializer, QuestionSerializer, AnswerSerializer, QuizSubmitSerializer, QuestionDetailSerializer, SingleAnswerSubmissionSerializer,
                             CancelEnrollmentSerializer)
from main.models import (Category, Course, Day, EduType, Enrollment, Event,
                         Level, Teacher, Unit, QuizType, Quiz, Question, Answer)

# ─── EduType / Category / Level / Day ─────────────────────────────────────


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_summary="List all education types", tags=["EduType"]
    ),
)
@method_decorator(
    name="create",
    decorator=swagger_auto_schema(
        operation_summary="Create a new education type (Superuser only)",
        tags=["EduType"],
    ),
)
class EduTypeViewSet(viewsets.ModelViewSet):
    queryset = EduType.objects.all()
    serializer_class = EduTypeSerializer
    permission_classes = [IsSuperUserOrReadOnly]


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_summary="List all course categories", tags=["Category"]
    ),
)
@method_decorator(
    name="create",
    decorator=swagger_auto_schema(
        operation_summary="Create a new category (Superuser only)", tags=["Category"]
    ),
)
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsSuperUserOrReadOnly]


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_summary="List all course levels", tags=["Level"]
    ),
)
@method_decorator(
    name="create",
    decorator=swagger_auto_schema(
        operation_summary="Create a new course level (Superuser only)", tags=["Level"]
    ),
)
class LevelViewSet(viewsets.ModelViewSet):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    permission_classes = [IsSuperUserOrReadOnly]


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(operation_summary="List all week days", tags=["Day"]),
)
@method_decorator(
    name="create",
    decorator=swagger_auto_schema(
        operation_summary="Add a new week day (Superuser only)", tags=["Day"]
    ),
)
class DayViewSet(viewsets.ModelViewSet):
    queryset = Day.objects.all()
    serializer_class = DaySerializer
    permission_classes = [IsSuperUserOrReadOnly]


# ─── Teacher ────────────────────────────────────────────────────────────────


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_summary="List all teachers", tags=["Teacher"]
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        operation_summary="Retrieve a specific teacher", tags=["Teacher"]
    ),
)
class TeacherViewSet(viewsets.ModelViewSet):
    """
    SAFE_METHODS:  everyone (AllowAny).
    Non-safe:      EDU_CENTER or BRANCH only.
    """

    queryset = Teacher.objects.select_related("branch")
    serializer_class = TeacherSerializer
    permission_classes = [IsEduCenterBranchOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_authenticated:
            if user.role == "EDU_CENTER":
                return qs.filter(branch__edu_center__user=user)
            if user.role == "BRANCH":
                return qs.filter(branch__admins=user)
        # STUDENT / anon: see all
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        branch = serializer.validated_data["branch"]
        if user.role == "EDU_CENTER":
            if branch.edu_center.user != user:
                raise PermissionDenied(
                    "You may only add teachers to your own center’s branches."
                )
        else:  # BRANCH
            if user not in branch.admins.all():
                raise PermissionDenied("You may only add teachers to your own branch.")
        serializer.save()


# ─── Course ─────────────────────────────────────────────────────────────────


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_summary="List all courses",
        operation_description="Retrieve all courses with optional filters, search, ordering.",
        tags=["Course"],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        operation_summary="Retrieve a specific course", tags=["Course"]
    ),
)
@method_decorator(
    name="create",
    decorator=swagger_auto_schema(
        operation_summary="Create a new course (EDU_CENTER or BRANCH only)",
        tags=["Course"],
    ),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(
        operation_summary="Update an existing course", tags=["Course"]
    ),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_summary="Partially update a course", tags=["Course"]
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(operation_summary="Delete a course", tags=["Course"]),
)
class CourseViewSet(viewsets.ModelViewSet):
    queryset = (
        Course.objects.filter(is_archived=False)
        .select_related("branch", "branch__edu_center", "teacher", "category", "level")
        .prefetch_related("days")
    )
    serializer_class = CourseSerializer
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = CourseFilter
    search_fields = [
        "name",
        "branch__edu_center__name",
        "teacher__name",
        "category__name",
    ]
    ordering_fields = ["price", "total_places", "start_date"]
    ordering = ["start_date"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        if self.action in ["apply", "my_courses"]:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsEduCenterBranchOrReadOnly()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_authenticated:
            if user.role == "EDU_CENTER":
                return qs.filter(branch__edu_center__user=user)
            if user.role == "BRANCH":
                return qs.filter(branch__admins=user)
        return qs

    @action(detail=True, methods=["post"], serializer_class=EmptySerializer)
    def apply(self, request, pk=None):
        course = get_object_or_404(Course, pk=pk, is_archived=False)
        user = request.user
        if Enrollment.objects.filter(user=user, course=course).exists():
            return Response(
                {"detail": "Already applied."}, status=status.HTTP_400_BAD_REQUEST
            )
        Enrollment.objects.create(user=user, course=course)
        return Response(
            {
                "detail": "Applied successfully.",
                "course_id": course.id,
                "user_id": user.id,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="my-courses", url_name="my_courses")
    def my_courses(self, request):
        qs = (
            Enrollment.objects.filter(user=request.user)
            .select_related("course__level")
            .prefetch_related("course__days")
        )
        ser = MyCourseSerializer(qs, many=True, context={"request": request})
        return Response(ser.data)


# ─── Event ──────────────────────────────────────────────────────────────────


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_summary="List all events",
        operation_description="Retrieve all upcoming events.",
        tags=["Event"],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        operation_summary="Retrieve a specific event", tags=["Event"]
    ),
)
@method_decorator(
    name="create",
    decorator=swagger_auto_schema(
        operation_summary="Create a new event (EDU_CENTER or BRANCH only)",
        tags=["Event"],
    ),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(operation_summary="Update an event", tags=["Event"]),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(operation_summary="Delete an event", tags=["Event"]),
)
class EventViewSet(viewsets.ModelViewSet):
    """
    SAFE_METHODS: everyone
    Others:       EDU_CENTER or BRANCH
    """

    queryset = (
        Event.objects.filter(is_archived=False)
        .select_related("edu_center", "branch")
        .prefetch_related("categories")
    )
    serializer_class = EventSerializer
    permission_classes = [IsEduCenterBranchOrReadOnly]
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = EventFilter
    search_fields = ["name", "description"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_authenticated:
            if user.role == "EDU_CENTER":
                return qs.filter(edu_center__user=user)
            if user.role == "BRANCH":
                return qs.filter(branch__admins=user)
        # STUDENT / anon: see all
        return qs


# ─── Filter Schema endpoints ────────────────────────────────────────────────


class CourseFilterSchemaView(APIView):
    def get(self, request):
        return Response(
            {
                "price_min": ">= price",
                "price_max": "<= price",
                "total_places_min": ">= total places",
                "total_places_max": "<= total places",
                "teacher_gender": "male/female",
                "edu_center": "center ID",
                "category": "category ID",
            }
        )


class EventFilterSchemaView(APIView):
    def get(self, request):
        return Response(
            {
                "start_date": "from YYYY-MM-DD",
                "end_date": "to YYYY-MM-DD",
                "edu_center_id": "comma–separated center IDs",
                "category": "category filter",
            }
        )


class AppliedStudentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only list of enrollments visible to the current user,
    plus /stats/, /{pk}/confirm/ and /{pk}/cancel/ endpoints.
    """
    serializer_class = AppliedStudentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination

    filter_backends = [
        DjangoFilterBackend,SearchFilter,OrderingFilter,
    ]
    filterset_fields = ["status", "course", "course__branch"]
    search_fields = ["user__full_name", "user__phone_number"]
    ordering_fields = ["applied_at", "user__full_name"]
    ordering = ["-applied_at"]

    def get_queryset(self):
        user = self.request.user
        qs = Enrollment.objects.select_related(
            "user",
            "course",
            "course__branch",
            "course__branch__edu_center"
        )
        if user.role == Enrollment.Status.PENDING:
            return qs.filter(status=Enrollment.Status.PENDING)
        if user.role == "EDU_CENTER":
            return qs.filter(course__branch__edu_center__user=user)
        if user.role == "BRANCH":
            return qs.filter(course__branch__admins=user)
        return qs.none()

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        """
        GET /api/applied-students/stats/
        Returns total/pending/confirmed/canceled counts + 30-day trend.
        """
        qs = self.get_queryset()
        now = timezone.now()
        start_curr = now - timedelta(days=30)
        start_prev = now - timedelta(days=60)

        total = qs.count()
        pending = qs.filter(status=Enrollment.Status.PENDING).count()
        confirmed = qs.filter(status=Enrollment.Status.CONFIRMED).count()
        canceled = qs.filter(status=Enrollment.Status.CANCELED).count()

        past_30 = qs.filter(applied_at__gte=start_curr).count()
        prev_30 = qs.filter(
            applied_at__gte=start_prev,
            applied_at__lt=start_curr
        ).count()

        pct = None
        if prev_30:
            pct = round((past_30 - prev_30) / prev_30 * 100, 1)

        return Response({
            "total":     total,
            "pending":   pending,
            "confirmed": confirmed,
            "canceled":  canceled,
            "trend": {
                "past_30_days": past_30,
                "prev_30_days": prev_30,
                "pct_change":   pct
            }
        }, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["post"],
        url_path="confirm",
        permission_classes=[IsAuthenticated],
        serializer_class=AppliedStudentSerializer
    )
    def confirm(self, request, pk=None):
        """
        POST /api/applied-students/{pk}/confirm/
        Only valid for PENDING enrollments.
        Moves to CONFIRMED and updates course counts.
        """
        enrollment = self.get_object()
        if enrollment.status != Enrollment.Status.PENDING:
            return Response(
                {"detail": "Only pending enrollments can be confirmed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update course capacity
        course = enrollment.course
        course.booked_places = F("booked_places") + 1
        course.total_places = F("total_places") - 1
        course.save(update_fields=["booked_places", "total_places"])

        enrollment.status = Enrollment.Status.CONFIRMED
        enrollment.save(update_fields=["status"])

        return Response(
            AppliedStudentSerializer(enrollment, context={"request": request}).data,
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="cancel",
        permission_classes=[IsAuthenticated],
        serializer_class=CancelEnrollmentSerializer
    )
    def cancel(self, request, pk=None):
        """
        POST /api/applied-students/{pk}/cancel/
        Body: { "reason": "some text" }
        If previously CONFIRMED, reverts course counts,
        then marks enrollment as CANCELED.
        """
        enrollment = self.get_object()
        ser = CancelEnrollmentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        # If already confirmed, revert course counts
        if enrollment.status == Enrollment.Status.CONFIRMED:
            course = enrollment.course
            course.booked_places = F("booked_places") - 1
            course.total_places = F("total_places") + 1
            course.save(update_fields=["booked_places", "total_places"])

        enrollment.status = Enrollment.Status.CANCELED
        enrollment.cancelled_reason = ser.validated_data["reason"]
        enrollment.save(update_fields=["status", "cancelled_reason"])

        return Response(
            AppliedStudentSerializer(enrollment, context={"request": request}).data,
            status=status.HTTP_200_OK
        )


# Quiz viewsets


class UnitViewSet(viewsets.ModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsSuperUserOrReadOnly]


class QuizTypeViewSet(viewsets.ModelViewSet):
    queryset = QuizType.objects.all()
    serializer_class = QuizTypeSerializer
    permission_classes = [IsSuperUserOrReadOnly]


class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [IsSuperUserOrReadOnly]

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def questions(self, request, pk=None):
        """
        GET /api/quizzes/{pk}/questions/
        — quizning barcha savollarini va mumkin bo‘lgan javoblarini qaytaradi.
        """
        quiz = self.get_object()
        qs = quiz.questions.select_related().all()
        data = []
        for q in qs:
            data.append({
                'id': q.id,
                'text': q.text,
                'choices': [
                    {'id': a.id, 'text': a.text}
                    for a in q.answers.all()
                ]
            })
        return Response(data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        serializer_class=QuizSubmitSerializer,  
    )
    def submit(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answers = serializer.validated_data['answers']
        quiz = self.get_object()
        total = quiz.questions.count()
        correct = 0
        detail = []
        for item in answers:
            qid = item['question']
            aid = item['answer']
            try:
                a = quiz.questions.get(pk=qid).answers.get(pk=aid)
            except:
                continue
            is_corr = a.correct
            detail.append({
                'question': qid,
                'answer':   aid,
                'correct':  is_corr
            })
            if is_corr:
                correct += 1

        return Response({
            'total': total,
            'correct': correct,
            'detail': detail,
            'percent': round(correct/total*100, 2)
        })


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.select_related('quiz')
    serializer_class = QuestionSerializer
    permission_classes = [IsSuperUserOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return QuestionDetailSerializer
        return super().get_serializer_class()

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        serializer_class=SingleAnswerSubmissionSerializer,
        url_path='submit-answer'
    )
    def submit_answer(self, request, pk=None):
        question = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ans_id = serializer.validated_data['answer']

        try:
            ans = question.answers.get(pk=ans_id)
        except Answer.DoesNotExist:
            return Response(
                {'detail': 'Invalid answer id for this question.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            'question': question.id,
            'selected_answer': ans.id,
            'correct': ans.correct
        })


class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.select_related('question')
    serializer_class = AnswerSerializer
    permission_classes = [IsSuperUserOrReadOnly]

