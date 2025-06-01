from djoser.serializers import UserSerializer as BaseUserSerializer, UserCreateSerializer as BaseUserCreateSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from api.serializers import EducationCenterSerializer

from main.models import Branch, EducationCenter

User = get_user_model()


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        fields = ['id', 'username', 'full_name', 'password', 'role']
        read_only_fields = ['role']

    def validate(self, attrs):
        if attrs.get("phone_number"):
            attrs["role"] = "STUDENT"
        return super().validate(attrs)


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = ['id', 'username', 'full_name', 'phone_number',
                  'birth_date', 'gender', 'country', 'region', 'city', ]


class EduCenterCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    education_center = EducationCenterSerializer(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name',
                  'password', 'education_center']

    def create(self, validated_data):
        edu_center_data = validated_data.pop('education_center')
        edu_type_data = edu_center_data.pop('edu_type', [])
        category_data = edu_center_data.pop('categories', [])
        user = User.objects.create_user(
            username=validated_data['username'],
            full_name=validated_data['full_name'],
            password=validated_data['password'],
            role='EDU_CENTER'
        )

        edu_center = EducationCenter.objects.create(
            user=user, **edu_center_data)
        if edu_type_data:
            edu_center.edu_type.set(edu_type_data)
        if category_data:
            edu_center.categories.set(category_data)

        return user


class BranchCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    latitude = serializers.DecimalField(
        max_digits=10, decimal_places=7, required=True)
    longitude = serializers.DecimalField(
        max_digits=11, decimal_places=7, required=True)

    phone_number = serializers.CharField(
        required=True,
        validators=[
            RegexValidator(
                regex=r'^\+?998\d{9}$',
                message="Telefon raqam quyidagi formatda bo‘lishi kerak: +998901234567"
            )
        ]
    )

    work_time = serializers.CharField(required=True)

    google_map = serializers.SerializerMethodField(read_only=True)
    yandex_map = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Branch
        fields = [
            'id', 'name', 'latitude', 'longitude',
            'phone_number', 'work_time',
            'username', 'password',
            'google_map', 'yandex_map'
        ]

    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        edu_center = validated_data.pop('edu_center')

        branch_user = User.objects.create_user(
            username=username,
            full_name=validated_data['name'],
            password=password,
            role='BRANCH'
        )

        branch = Branch.objects.create(edu_center=edu_center, **validated_data)
        branch.admins.add(branch_user)
        return branch

    def get_google_map(self, obj):
        if obj.latitude and obj.longitude:
            return f"https://www.google.com/maps/dir/?api=1&destination={obj.latitude},{obj.longitude}"
        return None

    def get_yandex_map(self, obj):
        if obj.latitude and obj.longitude:
            return f"https://yandex.com/maps/?rtext=~{obj.latitude},{obj.longitude}"
        return None
