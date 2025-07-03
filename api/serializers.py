from datetime import timedelta
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from main.models import (Branch, Category, Course, Day, EducationCenter,
                         EduType, Enrollment, Event, Level, Like, Teacher,
                         View, Banner)


class DynamicBranchSerializerMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated or "branch" not in self.fields:
            return

        if user.role == "EDU_CENTER":
            self.fields["branch"] = serializers.PrimaryKeyRelatedField(
                queryset=Branch.objects.filter(edu_center__user=user),
                required=True,
            )
        elif user.role == "BRANCH":
            branch = user.branches.first()
            if not branch:
                raise serializers.ValidationError(
                    "Sizga biriktirilgan filial topilmadi.")
            self.fields["branch"] = serializers.HiddenField(default=branch)
        else:
            self.fields["branch"] = serializers.PrimaryKeyRelatedField(
                queryset=Branch.objects.none(), required=False
            )


class EducationCenterSerializer(serializers.ModelSerializer):
    likes_count = serializers.IntegerField(read_only=True)
    views_count = serializers.IntegerField(read_only=True)
    categories = serializers.SerializerMethodField()

    class Meta:
        model = EducationCenter
        fields = [
            "id",
            "name",
            "description",
            "country",
            "region",
            "city",
            "phone_number",
            "edu_type",
            "categories",
            "logo",
            "cover",
            "instagram_link",
            "telegram_link",
            "facebook_link",
            "website_link",
            "likes_count",
            "views_count",
        ]

    def get_categories(self, obj):
        cats = set()
        for br in obj.branches.all():
            for cr in br.courses.all():
                if cr.category:
                    cats.add(cr.category.name)
        return list(cats)


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ["id", "user", "liked_at"]
        read_only_fields = ["user", "liked_at"]


class ViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = View
        fields = ["id", "user", "viewed_at"]


class EduTypeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = EduType
        fields = ["id", "name"]


class LevelSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        source='category',
        queryset=Category.objects.all(),
        write_only=True
    )
    category = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Level
        fields = ['id', 'name', 'category_id', 'category']

    def get_category(self, obj):
        return {
            'id':   obj.category.id,
            'name': obj.category.name
        } if obj.category else None


class CategorySerializer(serializers.ModelSerializer):
    levels = LevelSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'levels']


class DaySerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(source="get_name_display", read_only=True)

    class Meta:
        model = Day
        fields = ["id", "name", "display_name"]
        read_only_fields = ["id", "display_name"]


class TeacherSerializer(DynamicBranchSerializerMixin, serializers.ModelSerializer):
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(), required=True)
    branch_id = serializers.IntegerField(source="branch.id", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = Teacher
        fields = ["id", "full_name", "gender", "branch", "branch_id", "branch_name"]

    def get_branch_name(self, obj):
        return obj.branch.name if obj.branch and obj.branch.name else None


class CourseEnrollmentStudentSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    phone_number = serializers.CharField(source="user.phone_number", read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "full_name", "phone_number", "status"]


class CourseSerializer(serializers.ModelSerializer):
    days = serializers.CharField(
        required=False,
        help_text='Comma-separated days, e.g. "Sun,Sat,Fri"'
    )

    # ─── Your FK _id fields for writes & their read-only names ────────────
    branch_id = serializers.PrimaryKeyRelatedField(
        source="branch",   queryset=Branch.objects.all())
    branch_name = serializers.CharField(source="branch.name",          read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source="category", queryset=Category.objects.all())
    category_name = serializers.CharField(source="category.name",        read_only=True)
    level_id = serializers.PrimaryKeyRelatedField(
        source="level",    queryset=Level.objects.all())
    level_name = serializers.CharField(source="level.name",           read_only=True)
    teacher_id = serializers.PrimaryKeyRelatedField(
        source="teacher",  queryset=Teacher.objects.all())
    teacher_name = serializers.CharField(source="teacher.full_name",    read_only=True)
    teacher_gender = serializers.CharField(
        source="teacher.gender",       read_only=True)

    # ─── Pricing & computed read-only fields ─────────────────────────────
    final_price = serializers.DecimalField(
        read_only=True, max_digits=10, decimal_places=2)
    available_places = serializers.IntegerField(read_only=True)
    duration_months = serializers.SerializerMethodField()
    work_time = serializers.CharField(source="branch.work_time", read_only=True)

    # ─── Media & map fields ───────────────────────────────────────────────
    edu_center_logo = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    phone_number = serializers.CharField(
        source="branch.phone_number",                 read_only=True)
    telegram_link = serializers.CharField(
        source="branch.edu_center.telegram_link",     read_only=True)
    google_map = serializers.SerializerMethodField()
    yandex_map = serializers.SerializerMethodField()

    # ─── Prefetched students ──────────────────────────────────────────────
    students = CourseEnrollmentStudentSerializer(
        many=True, read_only=True, source="prefetched_enrollments"
    )

    class Meta:
        model = Course
        fields = [
            "id", "name", "is_archived",



            # foreign keys
            "branch_id", "branch_name",
            "category_id", "category_name",
            "level_id", "level_name",
            "teacher_id", "teacher_name", "teacher_gender",

            # days (string in, list out)
            "days",

            # scheduling & pricing
            "start_date", "end_date", "total_places",
            "price", "discount", "start_time", "end_time", "intensive",
            "final_price", "available_places", "duration_months", "work_time",

            # media & mapping
            "edu_center_logo", "cover",
            "latitude", "longitude",
            "phone_number", "telegram_link",
            "google_map", "yandex_map",

            # students
            "students",
        ]
        read_only_fields = [
            "id", "branch_name", "category_name", "level_name", "teacher_name",
            "teacher_gender", "final_price", "available_places",
            "duration_months", "work_time", "edu_center_logo", "cover",
            "latitude", "longitude", "phone_number", "telegram_link",
            "google_map", "yandex_map", "students"
        ]

    def _abbr_to_value(self):
        return {
            label[:3].capitalize(): value
            for value, label in Day.DayChoices.choices
        }

    def create(self, validated_data):
        days_csv = validated_data.pop("days", None)
        course = super().create(validated_data)
        if isinstance(days_csv, str):
            mapping = self._abbr_to_value()
            abbrs = [d.strip() for d in days_csv.split(",") if d.strip()]
            vals = [mapping[a] for a in abbrs if a in mapping]
            course.days.set(Day.objects.filter(name__in=vals))
        return course

    def update(self, instance, validated_data):
        days_csv = validated_data.pop("days", None)
        course = super().update(instance, validated_data)
        if isinstance(days_csv, str):
            mapping = self._abbr_to_value()
            abbrs = [d.strip() for d in days_csv.split(",") if d.strip()]
            vals = [mapping[a] for a in abbrs if a in mapping]
            course.days.set(Day.objects.filter(name__in=vals))
        return course

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["days"] = [
            d.get_name_display()[:3].capitalize()
            for d in instance.days.all()
        ]
        return data

    # ─── other SerializerMethodFields ───────────────────────────────────
    def get_duration_months(self, obj):
        if obj.start_date and obj.end_date:
            d = relativedelta(obj.end_date, obj.start_date)
            return d.years * 12 + d.months + (1 if d.days > 0 else 0)
        return None

    def get_edu_center_logo(self, obj):
        req = self.context.get("request")
        logo = getattr(obj.branch.edu_center, "logo", None)
        return req.build_absolute_uri(logo.url) if logo and req else getattr(logo, "url", None)

    def get_cover(self, obj):
        req = self.context.get("request")
        cov = getattr(obj.branch.edu_center, "cover", None)
        return req.build_absolute_uri(cov.url) if cov and req else getattr(cov, "url", None)

    def get_latitude(self, obj):
        return float(obj.branch.latitude) if obj.branch and obj.branch.latitude else None

    def get_longitude(self, obj):
        return float(obj.branch.longitude) if obj.branch and obj.branch.longitude else None

    def get_google_map(self, obj):
        lat, lng = obj.branch.latitude, obj.branch.longitude
        if lat and lng:
            return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"
        return None

    def get_yandex_map(self, obj):
        lat, lng = obj.branch.latitude, obj.branch.longitude
        if lat and lng:
            return f"https://yandex.com/maps/?rtext=~{lat},{lng}"
        return None


class EventSerializer(DynamicBranchSerializerMixin, serializers.ModelSerializer):
    edu_center_name = serializers.SerializerMethodField(read_only=True)
    edu_center_logo = serializers.SerializerMethodField(read_only=True)
    category_names = serializers.SerializerMethodField(read_only=True)
    phone_number = serializers.SerializerMethodField(read_only=True)
    telegram_link = serializers.SerializerMethodField(read_only=True)
    branch_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "name",
            "picture",
            "date",
            "start_time",
            "requirements",
            "price",
            "description",
            "link",
            "branch_name",
            "phone_number",
            "edu_center_name",
            "edu_center_logo",
            "category_names",
            "is_archived",
            "telegram_link",
        ]

    def get_edu_center_name(self, obj):
        return (
            obj.branch.edu_center.name if obj.branch and obj.branch.edu_center else None
        )

    def get_phone_number(self, obj):
        return (
            obj.branch.phone_number if obj.branch and obj.branch.phone_number else None
        )

    def get_telegram_link(self, obj):
        return (
            obj.branch.telegram_link
            if obj.branch and obj.branch.telegram_link
            else None
        )

    def get_branch_name(self, obj):
        return obj.branch.name if obj.branch and obj.branch.name else None

    def get_edu_center_logo(self, obj):
        ec = getattr(obj.branch, "edu_center", None)
        if not ec or not ec.logo:
            return None
        request = self.context.get("request")
        url = ec.logo.url
        return request.build_absolute_uri(url) if request else url

    def get_category_names(self, obj):
        return [cat.name for cat in obj.categories.all()]

    def create(self, validated_data):
        categories = validated_data.pop("categories", [])
        branch = validated_data["branch"]
        validated_data["edu_center"] = branch.edu_center
        event = super().create(validated_data)
        event.categories.set(categories)
        return event


class TeacherDashboardSerializer(serializers.ModelSerializer):
    branch = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = Teacher
        fields = ["id", "name", "gender", "branch"]


class EventDashboardSerializer(serializers.ModelSerializer):
    branch = serializers.CharField(source="branch.name", read_only=True)
    edu_center = serializers.CharField(source="edu_center.name", read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "name",
            "picture",
            "date",
            "start_time",
            "requirements",
            "price",
            "branch",
            "edu_center",
        ]


class StatItemSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    past_30_days = serializers.IntegerField()
    prev_30_days = serializers.IntegerField()
    pct_change = serializers.FloatField(allow_null=True)


class EnrollmentStatusStatsSerializer(serializers.Serializer):
    total = StatItemSerializer()
    confirmed = StatItemSerializer()
    pending = StatItemSerializer()
    canceled = StatItemSerializer()


class AppliedStudentSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name",       read_only=True)
    phone_number = serializers.CharField(source="user.phone_number",    read_only=True)
    course_id = serializers.IntegerField(source="course.id",         read_only=True)
    course_name = serializers.CharField(source="course.name",          read_only=True)
    status = serializers.CharField(read_only=True)
    reason = serializers.CharField(
        source="cancelled_reason",
        read_only=True,
        allow_blank=True,
        allow_null=True
    )
    branch_name = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "full_name",
            "phone_number",
            "course_id",
            "course_name",
            "applied_at",
            "status",
            "reason",
            "branch_name",
        ]
        read_only_fields = fields

    def get_branch_name(self, obj):
        branch = obj.course.branch
        return branch.name if branch else None


class CancelEnrollmentSerializer(serializers.Serializer):
    reason = serializers.CharField(
        help_text="Reason for cancellation",
        allow_blank=False
    )


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ["id", "image", "language_code"]
        read_only_fields = ["id"]
