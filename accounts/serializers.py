from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers

from api.serializers import EducationCenterSerializer
from main.models import Branch, EducationCenter, Enrollment

User = get_user_model()


class UserCreateSerializer(BaseUserCreateSerializer):
    re_password = serializers.CharField(write_only=True)

    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = [
            "id",
            "full_name",
            "phone_number",
            "password",
            "re_password",
            "role",
        ]
        read_only_fields = ["role"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(
                "Bu telefon raqam bilan ro‘yxatdan oʻtilgan foydalanuvchi "
                "allaqachon mavjud."
            )
        return value

    def validate(self, attrs):
        password = attrs.get("password")
        re_password = attrs.pop("re_password", None)

        if password != re_password:
            raise serializers.ValidationError(
                {"password": "Parol va takroriy parol mos kelmadi."}
            )

        if attrs.get("phone_number"):
            attrs["role"] = "STUDENT"

        return super().validate(attrs)

    def create(self, validated_data):
        return super().create(validated_data)


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = [
            "id",
            "username",
            "full_name",
            "phone_number",
            "birth_date",
            "gender",
            "country",
            "region",
            "city",
            "role",
        ]
        read_only_fields = ["id", "username", "role"]


class EduCenterCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    education_center = EducationCenterSerializer(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "full_name", "password", "education_center"]

    def create(self, validated_data):
        edu_center_data = validated_data.pop("education_center")
        edu_type_data = edu_center_data.pop("edu_type", [])
        category_data = edu_center_data.pop("categories", [])
        user = User.objects.create_user(
            username=validated_data["username"],
            full_name=validated_data["full_name"],
            password=validated_data["password"],
            role="EDU_CENTER",
        )

        edu_center = EducationCenter.objects.create(user=user, **edu_center_data)
        if edu_type_data:
            edu_center.edu_type.set(edu_type_data)
        if category_data:
            edu_center.categories.set(category_data)

        return user


class BranchCreateSerializer(serializers.ModelSerializer):

    latitude = serializers.DecimalField(max_digits=10, decimal_places=7, required=True)
    longitude = serializers.DecimalField(max_digits=11, decimal_places=7, required=True)

    phone_number = serializers.CharField()

    work_time = serializers.CharField(required=True)

    google_map = serializers.SerializerMethodField(read_only=True)
    yandex_map = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Branch
        fields = [
            "id",
            "name",
            "latitude",
            "longitude",
            "phone_number",
            "work_time",
            "google_map",
            "yandex_map",
        ]


    def get_google_map(self, obj):
        if obj.latitude and obj.longitude:
            return f"https://www.google.com/maps/dir/?api=1&destination={obj.latitude},{obj.longitude}"
        return None

    def get_yandex_map(self, obj):
        if obj.latitude and obj.longitude:
            return f"https://yandex.com/maps/?rtext=~{obj.latitude},{obj.longitude}"
        return None


class MyCourseSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="course.id", read_only=True)
    course_name = serializers.CharField(source="course.name", read_only=True)
    level = serializers.CharField(source="course.level.name", read_only=True)
    days = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    edu_center_logo = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = ["id", "course_name", "level", "days", "start_time", "edu_center_logo"]

    def get_days(self, obj):
        return [day.name[:3].capitalize() for day in obj.course.days.all()]

    def get_start_time(self, obj):
        return (
            obj.course.start_time.strftime("%H:%M") if obj.course.start_time else None
        )

    def get_edu_center_logo(self, obj):
        branch = getattr(obj.course, "branch", None)
        if not branch:
            return None
        edu_center = getattr(branch, "edu_center", None)
        if not edu_center:
            return None

        logo_field = getattr(edu_center, "logo", None)
        if not logo_field:
            return None

        request = self.context.get("request")
        logo_url = logo_field.url
        return request.build_absolute_uri(logo_url) if request else logo_url


class EmptySerializer(serializers.Serializer):
    pass
