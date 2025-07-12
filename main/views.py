import tablib
from datetime import datetime
from datetime import timedelta
from django.http import HttpResponse
from django.db.models import F, Count, Q, Prefetch, DecimalField
from decimal import Decimal
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count, F, Value
from accounts.serializers import EmptySerializer, MyCourseSerializer
from accounts.permissions import IsEduCenter
from accounts.models import CenterPayment, MonthlyCenterReport, PaidAmountLog
from api.permissions import IsSuperUserOrReadOnly, IsAccountant
from api.filters import CourseFilter, EventFilter
from api.paginations import DefaultPagination
from api.permissions import IsEduCenterBranchOrReadOnly, IsSuperUserOrReadOnly, IsAccountant
from api.serializers import (AppliedStudentSerializer, CategorySerializer,
                             CourseSerializer, DaySerializer,
                             EduTypeSerializer, EventSerializer,
                             LevelSerializer, TeacherSerializer,
                             CancelEnrollmentSerializer, EnrollmentStatusStatsSerializer,
                             BannerSerializer, CenterPaymentSerializer, MonthlyCenterReportSerializer, 
                             AddPaymentSerializer, PaidAmountLogSerializer)
from main.models import (Category, Course, Day, EduType, Enrollment, Event,
                         Level, Teacher, Banner, EducationCenter)

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


class CenterPaymentViewSet(viewsets.ModelViewSet):
    queryset = CenterPayment.objects.select_related('edu_center').only(
        'id', 'edu_center__id', 'edu_center__name'
    )
    serializer_class = CenterPaymentSerializer
    permission_classes = [IsAuthenticated, IsAccountant]
    http_method_names = ['get', 'post']

    @swagger_auto_schema(operation_summary="List center payments with summary stats")
    def list(self, request, *args, **kwargs):
        for center in EducationCenter.objects.only('id').all():
            CenterPayment.objects.get_or_create(edu_center=center)

        response = super().list(request, *args, **kwargs)

        total_paid = sum([cp.paid_amount for cp in CenterPayment.objects.only('paid_amount')])
        enroll_stats = Enrollment.objects.aggregate(
            total_apps=Count('id'),
            sum_payable=Sum(F('course__price') * Value(0.03), output_field=DecimalField())
        )
        total_debt = max((enroll_stats['sum_payable'] or Decimal("0.00")) - total_paid, Decimal("0.00"))

        response.data = {
            "overall": {
                "total_applications": enroll_stats['total_apps'] or 0,
                "total_payable": enroll_stats['sum_payable'] or 0,
                "total_paid": total_paid,
                "total_debt": total_debt,
            },
            "centers": response.data
        }
        return response

    @swagger_auto_schema(
        method='post',
        request_body=AddPaymentSerializer,
        operation_summary="Add new paid amount log"
    )
    @action(detail=True, methods=['post'], serializer_class=AddPaymentSerializer)
    def add_payment(self, request, pk=None):
        payment = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data['amount']
        PaidAmountLog.objects.create(center_payment=payment, amount=amount)

        data = CenterPaymentSerializer(payment, context={"request": request}).data
        return Response(data, status=status.HTTP_201_CREATED)


class PaidAmountLogViewSet(viewsets.ModelViewSet):
    queryset = PaidAmountLog.objects.select_related('center_payment', 'center_payment__edu_center').only(
        'id', 'amount', 'created_at', 'updated_at', 'center_payment__id'
    )
    serializer_class = PaidAmountLogSerializer
    permission_classes = [IsAuthenticated, IsAccountant]

    def perform_update(self, serializer):
        serializer.save(updated_at=timezone.now())


class MonthlyCenterReportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MonthlyCenterReport.objects.select_related('edu_center').only(
        'id', 'edu_center__id', 'edu_center__name',
        'year', 'month', 'total_applications',
        'payable_amount', 'paid_amount', 'debt'
    )
    serializer_class = MonthlyCenterReportSerializer
    permission_classes = [IsAuthenticated, IsAccountant]

    @swagger_auto_schema(
        operation_summary="Filter monthly report by ?month=YYYY-MM",
        manual_parameters=[
            openapi.Parameter('month', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Format: YYYY-MM')
        ]
    )
    def get_queryset(self):
        qs = super().get_queryset()
        month_str = self.request.query_params.get("month")
        if month_str:
            try:
                year, month = map(int, month_str.split("-"))
                qs = qs.filter(year=year, month=month)
            except ValueError:
                return qs.none()
        return qs

    @swagger_auto_schema(operation_summary="Get current month's report")
    @action(detail=False, methods=["get"])
    def current(self, request):
        today = datetime.today()
        year, month = today.year, today.month
        qs = self.get_queryset().filter(year=year, month=month)
        ser = self.get_serializer(qs, many=True)
        return Response(ser.data)


class EduCenterReportView(APIView):
    permission_classes = [IsAuthenticated, IsEduCenter]

    @swagger_auto_schema(
        operation_summary="Get your center report (all time or filtered by ?month=YYYY-MM)",
        manual_parameters=[
            openapi.Parameter('month', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Format: YYYY-MM')
        ]
    )
    def get(self, request):
        user = request.user
        month_str = request.query_params.get("month")

        enrollments = Enrollment.objects.select_related(
            'user', 'course', 'course__branch', 'course__branch__edu_center'
        ).only(
            'applied_at', 'user__full_name', 'user__phone_number',
            'course__name', 'course__price', 'course__branch__name',
            'course__branch__edu_center__id'
        ).filter(course__branch__edu_center__user=user)

        if month_str:
            try:
                year, month = map(int, month_str.split("-"))
                enrollments = enrollments.filter(applied_at__year=year, applied_at__month=month)
            except Exception:
                return Response({"detail": "month=YYYY-MM formatda bo'lishi kerak."}, status=400)
        else:
            year = month = None

        edu_center = EducationCenter.objects.only('id', 'name').get(user=user)
        total_apps = enrollments.count()
        payable = enrollments.aggregate(
            s=Sum(F('course__price') * Value(0.03), output_field=DecimalField())
        )['s'] or Decimal("0.00")

        paid_logs = PaidAmountLog.objects.select_related(
            'center_payment', 'center_payment__edu_center'
        ).only(
            'id', 'amount', 'created_at', 'updated_at',
            'center_payment', 'center_payment__id',
            'center_payment__edu_center', 'center_payment__edu_center__id'
        ).filter(center_payment__edu_center=edu_center)
        if year and month:
            paid_logs = paid_logs.filter(created_at__year=year, created_at__month=month)

        paid_amount = sum([log.amount for log in paid_logs])
        debt = max(payable - paid_amount, Decimal("0.00"))

        log_data = PaidAmountLogSerializer(paid_logs.order_by('-created_at'), many=True).data
        app_data = [
            {
                "full_name": e.user.full_name,
                "phone_number": e.user.phone_number,
                "course_name": e.course.name,
                "branch_name": e.course.branch.name,
                "applied_at": e.applied_at.strftime("%Y-%m-%d %H:%M"),
                "course_price": str(e.course.price),
                "charge_percent": "3%",
                "charge": str(round(e.course.price * Decimal("0.03"), 2))
            }
            for e in enrollments
        ]

        return Response({
            "edu_center_id": edu_center.id,
            "edu_center_name": edu_center.name,
            "year": year,
            "month": month,
            "total_applications": total_apps,
            "payable_amount": payable,
            "paid_amount": paid_amount,
            "debt": debt,
            "logs": log_data,
            "enrollments": app_data,
        })


class EduCenterReportExportView(APIView):
    permission_classes = [IsAuthenticated, IsEduCenter]

    @swagger_auto_schema(
        operation_summary="Download current month's report as Excel",
        manual_parameters=[
            openapi.Parameter('month', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True, description='Format: YYYY-MM')
        ]
    )
    def get(self, request):
        user = request.user
        month_str = request.query_params.get("month")

        try:
            year, month = map(int, month_str.split("-"))
        except Exception:
            return Response({"detail": "month=YYYY-MM formatda bo'lishi kerak."}, status=400)

        enrollments = Enrollment.objects.select_related(
            'user', 'course', 'course__branch', 'course__branch__edu_center'
        ).only(
            'applied_at', 'user__full_name', 'user__phone_number',
            'course__name', 'course__price', 'course__branch__name'
        ).filter(
            course__branch__edu_center__user=user,
            applied_at__year=year,
            applied_at__month=month
        )

        dataset = tablib.Dataset()
        dataset.headers = [
            "Full Name", "Phone Number", "Course Name", "Branch Name",
            "Applied At", "Course Price", "Charge %", "Charge Amount"
        ]

        total = Decimal("0.00")

        for e in enrollments:
            full_name = e.user.full_name
            phone = e.user.phone_number
            course_name = e.course.name
            branch_name = e.course.branch.name
            applied_at = e.applied_at.strftime("%Y-%m-%d %H:%M")
            price = e.course.price
            percent = "3%"
            charge = round(price * Decimal("0.03"), 2)
            total += charge

            dataset.append([
                full_name, phone, course_name, branch_name,
                applied_at, price, percent, charge
            ])

        dataset.append_separator()
        dataset.append(["", "", "", "", "", "", "Total", total])

        response = HttpResponse(
            dataset.export("xlsx"),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f"attachment; filename=enrollments_{year}_{month}.xlsx"
        return response
    