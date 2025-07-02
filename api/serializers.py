from datetime import timedelta
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from main.models import (Branch, Category, Course, Day, EducationCenter,
                         EduType, Enrollment, Event, Level, Like, Teacher,
                         View, Unit, QuizType, Quiz, Question, Answer)


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
    final_price = serializers.DecimalField(
        read_only=True, max_digits=10, decimal_places=2)
    available_places = serializers.IntegerField(read_only=True)
    days = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    level_name = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()
    teacher_gender = serializers.SerializerMethodField()
    duration_months = serializers.SerializerMethodField()
    work_time = serializers.SerializerMethodField()
    edu_center_logo = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    telegram_link = serializers.SerializerMethodField()
    google_map = serializers.SerializerMethodField()
    yandex_map = serializers.SerializerMethodField()
    branch_id = serializers.IntegerField()
    category_id = serializers.IntegerField()
    teacher_id = serializers.IntegerField()
    level_id = serializers.IntegerField()
    students = CourseEnrollmentStudentSerializer(
        many=True,
        read_only=True,
        source="prefetched_enrollments"
    )

    days_input = serializers.CharField(
        write_only=True,
        required=False,
        help_text='Comma-separated days, e.g. "Sun,Sat,Fri"'
    )

    class Meta:
        model = Course
        fields = [
            "id", "name", "is_archived",

            # writeable relationships
            "branch", "branch_name",
            "category", "category_name",
            "level", "level_name",
            "teacher", "teacher_name", "teacher_gender",
            "days", 'branch_id', 'category_id', 'teacher_id', 'level_id',

            # scheduling & pricing
            "start_date", "end_date",
            "total_places", "price", "discount",
            "start_time", "end_time", "intensive",
            "final_price", "available_places",
            "duration_months", "work_time", 'days_input',

            # media & mapping
            "edu_center_logo", "cover",
            "latitude", "longitude",
            "phone_number", "telegram_link",
            "google_map", "yandex_map",

            # students list
            "students",
        ]

    def to_internal_value(self, data):
        if isinstance(data, dict) and 'days' in data and isinstance(data['days'], str):
            data = data.copy()
            data['days_input'] = data.pop('days')
        return super().to_internal_value(data)

    def create(self, validated_data):
        days_csv = validated_data.pop('days_input', None)
        course = super().create(validated_data)
        if days_csv is not None:
            names = [d.strip() for d in days_csv.split(',') if d.strip()]
            course.days.set(Day.objects.filter(name__in=names))
        return course

    def update(self, instance, validated_data):
        days_csv = validated_data.pop('days_input', None)
        course = super().update(instance, validated_data)
        if days_csv is not None:
            names = [d.strip() for d in days_csv.split(',') if d.strip()]
            course.days.set(Day.objects.filter(name__in=names))
        return course

    def get_days(self, obj):
        return [day.name[:3].capitalize() for day in obj.days.all()]

    def get_branch_name(self, obj):
        if obj.branch and obj.branch.edu_center:
            return f"{obj.branch.name} – {obj.branch.edu_center.name}"
        return None

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_level_name(self, obj):
        return obj.level.name if obj.level else None

    def get_teacher_name(self, obj):
        return obj.teacher.full_name if obj.teacher else None

    def get_teacher_gender(self, obj):
        return obj.teacher.gender if obj.teacher else None

    def get_duration_months(self, obj):
        if obj.start_date and obj.end_date:
            d = relativedelta(obj.end_date, obj.start_date)
            months = d.years * 12 + d.months + (1 if d.days > 0 else 0)
            return months
        return None

    def get_work_time(self, obj):
        return obj.branch.work_time if obj.branch else None

    def get_edu_center_logo(self, obj):
        req = self.context.get("request")
        logo = getattr(obj.branch.edu_center, "logo", None)
        if logo and req:
            return req.build_absolute_uri(logo.url)
        return getattr(logo, "url", None)

    def get_cover(self, obj):
        req = self.context.get("request")
        cover = getattr(obj.branch.edu_center, "cover", None)
        if cover and req:
            return req.build_absolute_uri(cover.url)
        return getattr(cover, "url", None)

    def get_latitude(self, obj):
        return float(obj.branch.latitude) if obj.branch and obj.branch.latitude else None

    def get_longitude(self, obj):
        return float(obj.branch.longitude) if obj.branch and obj.branch.longitude else None

    def get_phone_number(self, obj):
        return obj.branch.phone_number if obj.branch else None

    def get_telegram_link(self, obj):
        return obj.branch.edu_center.telegram_link if obj.branch and obj.branch.edu_center else None

    def get_google_map(self, obj):
        if obj.branch and obj.branch.latitude and obj.branch.longitude:
            return f"https://www.google.com/maps/dir/?api=1&destination={obj.branch.latitude},{obj.branch.longitude}"
        return None

    def get_yandex_map(self, obj):
        if obj.branch and obj.branch.latitude and obj.branch.longitude:
            return f"https://yandex.com/maps/?rtext=~{obj.branch.latitude},{obj.branch.longitude}"
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


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['id', 'number', 'title', 'description', 'created_at', 'updated_at']


class QuizTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizType
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']


class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = [
            'id', 'unit', 'quiz_type', 'name', 'topic',
            'description', 'points', 'show_select',
            'audio', 'image'
        ]


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'quiz', 'position', 'text', 'end_text']


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'question', 'position', 'text', 'correct']


class AnswerSubmissionSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    answer = serializers.IntegerField()


class QuizSubmitSerializer(serializers.Serializer):
    answers = AnswerSubmissionSerializer(
        many=True,
        help_text="List of {question: int, answer: int}"
    )


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'position', 'text']


class QuestionDetailSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'quiz', 'position', 'text', 'end_text', 'answers']


class SingleAnswerSubmissionSerializer(serializers.Serializer):
    answer = serializers.IntegerField()
