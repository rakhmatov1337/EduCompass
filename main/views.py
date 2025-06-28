from datetime import timedelta
from django.db.models import F, Count, Q, Prefetch
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
from accounts.permissions import IsEduCenter
from api.permissions import IsSuperUserOrReadOnly
from api.filters import CourseFilter, EventFilter
from api.paginations import DefaultPagination
from api.permissions import IsEduCenterBranchOrReadOnly, IsSuperUserOrReadOnly
from api.serializers import (AppliedStudentSerializer, CategorySerializer,
                             CourseSerializer, DaySerializer,
                             EduTypeSerializer, EventSerializer,
                             LevelSerializer, TeacherSerializer, UnitSerializer, QuizTypeSerializer,
                             QuizSerializer, QuestionSerializer, AnswerSerializer, QuizSubmitSerializer, QuestionDetailSerializer, SingleAnswerSubmissionSerializer,
                             CancelEnrollmentSerializer, EnrollmentStatusStatsSerializer, CourseDashboardDetailSerializer)
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
    queryset = Teacher.objects.select_related("branch")
    serializer_class = TeacherSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated(), IsEduCenter()]

    def get_queryset(self):
        """
        EDU_CENTERs see only teachers in their own centers.
        BRANCH users see only teachers in their own branch.
        Others (anonymous) see all (list/retrieve only).
        """
        qs = super().get_queryset()
        user = self.request.user

        if user.is_authenticated:
            if user.role == "EDU_CENTER":
                return qs.filter(branch__edu_center__user=user)
            if user.role == "BRANCH":
                return qs.filter(branch__admins=user)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        branch = serializer.validated_data["branch"]
        if branch.edu_center.user != user:
            raise PermissionDenied(
                "You may only add teachers to your own center’s branches.")

        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        branch = serializer.validated_data.get("branch", serializer.instance.branch)
        if branch.edu_center.user != user:
            raise PermissionDenied("You may only move teachers to branches you own.")
        serializer.save()

    def perform_destroy(self, instance):
        instance.delete()


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
        Course.objects.filter()
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
        "teacher__full_name",
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
        course = get_object_or_404(Course, pk=pk)
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
    
    @action(detail=True, methods=["get"], url_path="stats")
    def stats(self, request, pk=None):
        course = self.get_object()
        qs = Enrollment.objects.filter(course=course)
        now = timezone.now()
        t0 = now - timedelta(days=30)
        t1 = now - timedelta(days=60)

        def compute(sub_qs):
            cnt = sub_qs.count()
            past = sub_qs.filter(applied_at__gte=t0).count()
            prev = sub_qs.filter(applied_at__gte=t1, applied_at__lt=t0).count()
            pct = round((past - prev) / prev * 100, 1) if prev else None
            return {
                "count": cnt,
                "past_30_days": past,
                "prev_30_days": prev,
                "pct_change": pct,
            }

        data = {
            "total": compute(qs),
            "confirmed": compute(qs.filter(status=Enrollment.Status.CONFIRMED)),
            "pending": compute(qs.filter(status=Enrollment.Status.PENDING)),
            "canceled": compute(qs.filter(status=Enrollment.Status.CANCELED)),
        }

        return Response(data, status=status.HTTP_200_OK)



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


class CourseDashboardDetailViewSet(viewsets.ModelViewSet):
    serializer_class = CourseDashboardDetailSerializer
    permission_classes = [IsAuthenticated]
    queryset = Course._base_manager.none()

    def get_queryset(self):
        user = self.request.user
        qs = Course._base_manager.all()

        if user.role == "EDU_CENTER":
            qs = qs.filter(branch__edu_center__user=user)
        elif user.role == "BRANCH":
            qs = qs.filter(branch__admins=user)
        else:
            return Course._base_manager.none()
        qs = qs.annotate(
            total_applied=Count("enrollments", distinct=True),
            pending_count=Count("enrollments", filter=Q(enrollments__status="PENDING")),
            confirmed_count=Count("enrollments", filter=Q(
                enrollments__status="CONFIRMED")),
            canceled_count=Count("enrollments", filter=Q(
                enrollments__status="CANCELED")),
        )
        qs = qs.select_related(
            "branch",
            "branch__edu_center",
            "branch__edu_center__user",
            "teacher",
            "level",
            "category",
        )
        qs = qs.prefetch_related(
            "days",
            Prefetch(
                "enrollments",
                queryset=Enrollment.objects.select_related("user"),
                to_attr="prefetched_enrollments"
            ),
        )

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
    plus:
      - GET  /api/applied-students/stats/
      - POST /api/applied-students/{pk}/confirm/
      - POST /api/applied-students/{pk}/cancel/
    """
    serializer_class = AppliedStudentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
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

    @action(
        detail=False,
        methods=["get"],
        url_path="stats",
        serializer_class=EnrollmentStatusStatsSerializer
    )
    def stats(self, request):
        qs = self.get_queryset()
        now = timezone.now()
        t0 = now - timedelta(days=30)
        t1 = now - timedelta(days=60)

        def compute(sub_qs):
            cnt = sub_qs.count()
            past = sub_qs.filter(applied_at__gte=t0).count()
            prev = sub_qs.filter(applied_at__gte=t1, applied_at__lt=t0).count()
            pct = round((past - prev) / prev * 100, 1) if prev else None
            return {
                "count":        cnt,
                "past_30_days": past,
                "prev_30_days": prev,
                "pct_change":   pct,
            }

        data = {
            "total":     compute(qs),
            "confirmed": compute(qs.filter(status=Enrollment.Status.CONFIRMED)),
            "pending":   compute(qs.filter(status=Enrollment.Status.PENDING)),
            "canceled":  compute(qs.filter(status=Enrollment.Status.CANCELED)),
        }

        ser = self.get_serializer(data=data)
        ser.is_valid(raise_exception=True)
        return Response(ser.data, status=status.HTTP_200_OK)

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
        Only pending enrollments can be confirmed. Updates course counts
        and clears any previous cancellation reason.
        """
        enrollment = self.get_object()
        course = enrollment.course
        course.booked_places = F("booked_places") + 1
        course.total_places = F("total_places") - 1
        course.save(update_fields=["booked_places", "total_places"])
        enrollment.status = Enrollment.Status.CONFIRMED
        enrollment.cancelled_reason = ""
        enrollment.save(update_fields=["status", "cancelled_reason"])

        out = AppliedStudentSerializer(enrollment, context={"request": request})
        return Response(out.data, status=status.HTTP_200_OK)

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
        Body: { "reason": "…" }
        Reverts counts if it was confirmed, sets status and reason.
        """
        enrollment = self.get_object()
        ser = CancelEnrollmentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        if enrollment.status == Enrollment.Status.CONFIRMED:
            course = enrollment.course
            course.booked_places = F("booked_places") - 1
            course.total_places = F("total_places") + 1
            course.save(update_fields=["booked_places", "total_places"])

        enrollment.status = Enrollment.Status.CANCELED
        enrollment.cancelled_reason = ser.validated_data["reason"]
        enrollment.save(update_fields=["status", "cancelled_reason"])

        out = AppliedStudentSerializer(enrollment, context={"request": request})
        return Response(out.data, status=status.HTTP_200_OK)


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
