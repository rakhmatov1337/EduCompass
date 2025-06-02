from rest_framework import serializers
from dateutil.relativedelta import relativedelta


from main.models import *


class EducationCenterSerializer(serializers.ModelSerializer):
    likes_count = serializers.IntegerField(read_only=True)
    views_count = serializers.IntegerField(read_only=True)
    categories = serializers.SerializerMethodField()

    class Meta:
        model = EducationCenter
        fields = [
            'id', 'name', 'description', 'country', 'region', 'city',
            'phone_number', 'edu_type', 'categories',
            'logo', 'cover', 'instagram_link', 'telegram_link',
            'facebook_link', 'website_link', 'likes_count', 'views_count'
        ]

    def get_categories(self, obj):
        categories = set()
        for branch in obj.branches.all():
            for course in branch.courses.all():
                if course.category:
                    categories.add(course.category.name)
        return list(categories)


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'user', 'liked_at']
        read_only_fields = ['user', 'liked_at']


class ViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = View
        fields = ['id', 'user', 'viewed_at']


class EduTypeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = EduType
        fields = [
            'id', 'name'
        ]


class CategorySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = [
            'id', 'name'
        ]


class LevelSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Level
        fields = [
            'id', 'name'
        ]


class DaySerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(
        source='get_name_display', read_only=True)

    class Meta:
        model = Day
        fields = ['id', 'name', 'display_name']
        read_only_fields = ['id', 'display_name']


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ['id', 'name', 'gender', 'branch']


class CourseSerializer(serializers.ModelSerializer):
    final_price = serializers.DecimalField(
        read_only=True, max_digits=10, decimal_places=2)
    available_places = serializers.IntegerField(read_only=True)

    branch_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    level_name = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()
    teacher_gender = serializers.SerializerMethodField()
    days = serializers.SerializerMethodField()
    duration_months = serializers.SerializerMethodField()

    edu_center_logo = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()

    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    telegram_link = serializers.SerializerMethodField()
    branch_id = serializers.IntegerField(source='branch.id', read_only=True)
    category_id = serializers.IntegerField(
        source='category.id', read_only=True)
    level_id = serializers.IntegerField(source='level.id', read_only=True)
    teacher_id = serializers.IntegerField(source='teacher.id', read_only=True)

    google_map = serializers.SerializerMethodField()
    yandex_map = serializers.SerializerMethodField()
    work_time = serializers.SerializerMethodField()

    class Meta:
        model = Course
        exclude = ['is_archived', 'branch', 'category', 'level', 'teacher']

    def get_branch_name(self, obj):
        if obj.branch and obj.branch.edu_center:
            return f"{obj.branch.name} - {obj.branch.edu_center.name}"
        return None

    def get_work_time(self, obj):
        return obj.branch.work_time if obj.branch else None

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_level_name(self, obj):
        return obj.level.name if obj.level else None

    def get_teacher_name(self, obj):
        return obj.teacher.name if obj.teacher else None

    def get_teacher_gender(self, obj):
        return obj.teacher.gender if obj.teacher else None

    def get_days(self, obj):
        return [day.name[:3].capitalize() for day in obj.days.all()]

    def get_duration_months(self, obj):
        if obj.start_date and obj.end_date:
            delta = relativedelta(obj.end_date, obj.start_date)
            months = delta.years * 12 + delta.months
            if delta.days > 0:
                months += 1
            return months
        return None

    def get_edu_center_logo(self, obj):
        request = self.context.get('request')
        logo_url = obj.branch.edu_center.logo.url if obj.branch.edu_center.logo else None
        if request and logo_url:
            return request.build_absolute_uri(logo_url)
        return logo_url

    def get_cover(self, obj):
        request = self.context.get('request')
        cover_url = obj.branch.edu_center.cover.url if obj.branch.edu_center.cover else None
        if request and cover_url:
            return request.build_absolute_uri(cover_url)
        return cover_url

    def get_latitude(self, obj):
        return float(obj.branch.latitude) if obj.branch and obj.branch.latitude else None

    def get_longitude(self, obj):
        return float(obj.branch.longitude) if obj.branch and obj.branch.longitude else None

    def get_phone_number(self, obj):
        return obj.branch.phone_number if obj.branch and obj.branch.phone_number else None

    def get_telegram_link(self, obj):
        return obj.branch.edu_center.telegram_link if obj.branch and obj.branch.edu_center and obj.branch.edu_center.telegram_link else None

    def get_google_map(self, obj):
        if obj.branch and obj.branch.latitude and obj.branch.longitude:
            return f"https://www.google.com/maps/dir/?api=1&destination={obj.branch.latitude},{obj.branch.longitude}"
        return None

    def get_yandex_map(self, obj):
        if obj.branch and obj.branch.latitude and obj.branch.longitude:
            return f"https://yandex.com/maps/?rtext=~{obj.branch.latitude},{obj.branch.longitude}"
        return None


class EventSerializer(serializers.ModelSerializer):
    edu_center_logo = serializers.SerializerMethodField()
    edu_center_name = serializers.SerializerMethodField()
    telegram_link = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    google_map = serializers.SerializerMethodField()
    yandex_map = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    categories = serializers.StringRelatedField(many=True)

    class Meta:
        model = Event
        fields = [
            'id', 'name', 'picture', 'start_time', 'date',
            'requirements', 'price', 'description', 'link',
            'is_archived', 'latitude', 'longitude',
            'edu_center_name', 'edu_center_logo',
            'telegram_link', 'phone_number',
            'google_map', 'yandex_map',
            'categories'  # 👈 bu yerga ham qo‘shildi
        ]

    def get_edu_center_name(self, obj):
        return obj.edu_center.name if obj.edu_center else None

    def get_edu_center_logo(self, obj):
        request = self.context.get('request')
        logo_url = obj.edu_center.logo.url if obj.edu_center and obj.edu_center.logo else None
        if request and logo_url:
            return request.build_absolute_uri(logo_url)
        return logo_url

    def get_telegram_link(self, obj):
        return obj.edu_center.telegram_link if obj.edu_center and obj.edu_center.telegram_link else None

    def get_phone_number(self, obj):
        return obj.branch.phone_number if obj.branch and obj.branch.phone_number else None

    def get_google_map(self, obj):
        if obj.branch and obj.branch.latitude and obj.branch.longitude:
            return f"https://www.google.com/maps/dir/?api=1&destination={obj.branch.latitude},{obj.branch.longitude}"
        return None

    def get_yandex_map(self, obj):
        if obj.branch and obj.branch.latitude and obj.branch.longitude:
            return f"https://yandex.com/maps/?rtext=~{obj.branch.latitude},{obj.branch.longitude}"
        return None

    def get_latitude(self, obj):
        return float(obj.branch.latitude) if obj.branch and obj.branch.latitude else None

    def get_longitude(self, obj):
        return float(obj.branch.longitude) if obj.branch and obj.branch.longitude else None
