from drf_yasg import openapi
import os
import re
from datetime import datetime
from django.conf import settings
from rest_framework import generics
from datetime import timedelta
from django.db.models import F, Count, Q, Prefetch
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from decimal import Decimal
from django.db.models import Sum, Count, F, Value
from django.db.models.fields import DecimalField
from accounts.serializers import EmptySerializer, MyCourseSerializer
from accounts.permissions import IsEduCenter
from api.permissions import IsSuperUserOrReadOnly, IsAccountant
from api.filters import CourseFilter, EventFilter
from api.paginations import DefaultPagination
from api.permissions import IsEduCenterBranchOrReadOnly, IsSuperUserOrReadOnly
from api.serializers import (AppliedStudentSerializer, CategorySerializer,
                             CourseSerializer, DaySerializer,
                             EduTypeSerializer, EventSerializer,
                             LevelSerializer, TeacherSerializer,
                             CancelEnrollmentSerializer, EnrollmentStatusStatsSerializer, BannerSerializer, ExportReportSerializer, ExportStatsSerializer)
from main.models import (Category, Course, Day, EduType, Enrollment, Event,
                         Level, Teacher, Banner, Branch)

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
    queryset = Level.objects.select_related('category').all()
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
    queryset = Course.objects.select_related(
        "branch",
        "branch__edu_center",
        "teacher",
        "category",
        "level",
    ).prefetch_related(
        "days"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        data = getattr(self, 'initial_data', None)
        cat = data.get('category') if isinstance(data, dict) else None
        if cat:
            self.fields['level'].queryset = Level.objects.filter(category_id=cat)

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
                qs = qs.filter(branch__edu_center__user=user)
            elif user.role == "BRANCH":
                qs = qs.filter(branch__admins=user)

        qs = qs.annotate(
            total_applied=Count("enrollments", distinct=True),
            pending_count=Count("enrollments", filter=Q(enrollments__status="PENDING")),
            confirmed_count=Count("enrollments", filter=Q(
                enrollments__status="CONFIRMED")),
            canceled_count=Count("enrollments", filter=Q(
                enrollments__status="CANCELED")),
        )
        qs = qs.prefetch_related(
            Prefetch(
                "enrollments",
                queryset=Enrollment.objects.select_related("user"),
                to_attr="prefetched_enrollments"
            )
        )
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
        if getattr(self, 'swagger_fake_view', False):
            return Enrollment.objects.none()  # Swagger uchun bo‘sh queryset qaytaradi

        user = self.request.user
        qs = Enrollment.objects.select_related(
            "user",
            "course",
            "course__branch",
            "course__branch__edu_center"
        )

        if not user.is_authenticated:
            return qs.none()

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


class BannerViewSet(viewsets.ModelViewSet):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer
    permission_classes = [IsSuperUserOrReadOnly]


class ExportReportList(generics.ListAPIView):
    """
    GET /api/reports/
    Lists all Excel reports for the current user's edu_center.
    """
    serializer_class = ExportReportSerializer
    permission_classes = [IsEduCenter]

    @swagger_auto_schema(
        operation_summary="List available report files",
        responses={200: ExportReportSerializer(many=True)}
    )
    def get_queryset(self):
        edu_centers = getattr(self.request.user, "education_center", None)
        if not edu_centers:
            return []
        edu_center = edu_centers.first()
        if not edu_center:
            return []
        edu_center_id = edu_center.id
        exports_dir = os.path.join(settings.MEDIA_ROOT, "exports")
        pattern = re.compile(
            rf"^{edu_center_id}-.*-(\d{{4}}-\d{{2}}-\d{{2}})-applications\.xlsx$")
        reports = []
        for fname in os.listdir(exports_dir):
            m = pattern.match(fname)
            if m:
                date = datetime.strptime(m.group(1), "%Y-%m-%d").date()
                reports.append({"filename": fname, "date": date})
        # sort newest first
        return sorted(reports, key=lambda x: x["date"], reverse=True)


class ExportReportDownload(APIView):
    """
    GET /api/reports/{filename}/download/
    Returns the file as an attachment, only if it belongs to current edu_center.
    """
    permission_classes = [IsEduCenter]

    filename_param = openapi.Parameter(
        "filename",
        openapi.IN_PATH,
        description="Filename of the report to download",
        type=openapi.TYPE_STRING,
        example="1-Englishlife-2025-07-01-applications.xlsx"
    )

    @swagger_auto_schema(
        operation_summary="Download a report file",
        manual_parameters=[filename_param],
        responses={
            200: "File attachment (.xlsx)",
            404: "Not found"
        }
    )
    def get(self, request, filename):
        edu_centers = getattr(request.user, "education_center", None)
        if not edu_centers:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        edu_center = edu_centers.first()
        if not edu_center:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        edu_center_id = edu_center.id
        if not filename.startswith(f"{edu_center_id}-"):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        exports_dir = os.path.join(settings.MEDIA_ROOT, "exports")
        file_path = os.path.join(exports_dir, filename)
        if not os.path.exists(file_path):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        from django.http import FileResponse
        response = FileResponse(open(file_path, "rb"),
                                as_attachment=True, filename=filename)
        return response


class ExportStatsSummaryView(APIView):
    """
    Edu Center foydalanuvchisi uchun:
      - total_applications
      - payable_amount  (3% komissiya)
      - paid_amount     (hamisha 0)
      - debt            (payable - paid)
    branch bo‘yicha filterlash mumkin via ?branch=<id>
    """
    permission_classes = [IsEduCenter]

    branch_param = openapi.Parameter(
        "branch", openapi.IN_QUERY,
        description="Branch ID bo‘yicha filtrlash",
        type=openapi.TYPE_INTEGER,
        required=False,
    )

    @swagger_auto_schema(
        operation_summary="Edu Center statistics per branch",
        manual_parameters=[branch_param],
        responses={200: ExportStatsSerializer()}
    )
    def get(self, request):
        # 1) EduCenter olish
        edu_centers = getattr(request.user, "education_center", None)
        if not edu_centers:
            return Response({"detail": "Sizga tegishli o'quv markazi topilmadi"}, status=404)
        ec = edu_centers.first()
        if not ec:
            return Response({"detail": "Ta'lim markazi topilmadi"}, status=404)

        # 2) Branch filter
        branch_id = request.query_params.get("branch")
        courses = Course.objects.filter(branch__edu_center=ec)
        if branch_id:
            # xavfsizlik: shu edu_centerga tegishli branch ekanligini tekshirish
            if not Branch.objects.filter(id=branch_id, edu_center=ec).exists():
                return Response({"detail": "Bunday filialga ruxsat yoʻq"}, status=403)
            courses = courses.filter(branch_id=branch_id)

        # 3) Enrollment statistikasi
        enrollments = Enrollment.objects.filter(course__in=courses)
        total_applications = enrollments.count()
        payable_amount = sum(
            (e.course.price * Decimal("0.03") for e in enrollments if e.course.price),
            Decimal("0")
        )
        paid_amount = Decimal("0.00")
        debt = payable_amount - paid_amount

        data = {
            "edu_center_id":       ec.id,
            "edu_center_name":     ec.name,
            "total_applications":  total_applications,
            "payable_amount":      payable_amount.quantize(Decimal("0.01")),
            "paid_amount":         paid_amount.quantize(Decimal("0.01")),
            "debt":                debt.quantize(Decimal("0.01")),
        }
        serializer = ExportStatsSerializer(data, context={"request": request})
        return Response(serializer.data)


class AccountStatsView(APIView):
    """
    Buxgalter uchun:
      - GET  → barcha edu_centerlar bo‘yicha stats (paid_amount=0)
      - POST → "paid_amounts": { "<edu_center_id>": "<summa>" } qabul qilib qayta hisoblaydi
    """
    permission_classes = [IsAccountant]

    @swagger_auto_schema(
        operation_summary="Get all education center stats (unpaid)",
        responses={200: ExportStatsSerializer(many=True)}
    )
    def get(self, request):
        base = self._gather_base_stats()
        for rec in base:
            rec["paid_amount"] = Decimal("0.00").quantize(Decimal("0.01"))
        serializer = ExportStatsSerializer(
            base, many=True, context={"request": request})
        return Response(serializer.data)

    paid_param = openapi.Parameter(
        "paid_amounts", openapi.IN_BODY,
        description="{ edu_center_id: amount, … }",
        type=openapi.TYPE_OBJECT,
        example={"1": "100.00", "2": "50.00"}
    )

    @swagger_auto_schema(
        operation_summary="Post paid amounts and recalculate debt",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "paid_amounts": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    additional_properties=openapi.Schema(type=openapi.TYPE_STRING)
                )
            },
            required=["paid_amounts"]
        ),
        responses={200: ExportStatsSerializer(many=True)}
    )
    def post(self, request):
        paid_map = request.data.get("paid_amounts", {})
        base = self._gather_base_stats()
        for rec in base:
            pid = str(rec["edu_center_id"])
            paid = paid_map.get(pid, 0) or 0
            rec["paid_amount"] = Decimal(str(paid)).quantize(Decimal("0.01"))
        serializer = ExportStatsSerializer(
            base, many=True, context={"request": request})
        return Response(serializer.data)

    def _gather_base_stats(self):
        qs = (
            Enrollment.objects
            .values("course__branch__edu_center__id", "course__branch__edu_center__name")
            .annotate(
                total=Count("id"),
                payable=Sum(
                    F("course__price") * Value(0.03),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
            )
        )
        return [
            {
                "edu_center_id":      rec["course__branch__edu_center__id"],
                "edu_center_name":    rec["course__branch__edu_center__name"],
                "total_applications": rec["total"],
                "payable_amount":     rec["payable"].quantize(Decimal("0.01")),
            }
            for rec in qs
        ]
