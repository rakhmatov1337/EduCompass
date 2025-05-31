from rest_framework import serializers


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
    image = serializers.SerializerMethodField()

    class Meta:
        model = Course
        exclude = ['is_archived']

    def get_branch_name(self, obj):
        if obj.branch and obj.branch.edu_center:
            return f"{obj.branch.name} - {obj.branch.edu_center.name}"
        return None

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

    def get_image(self, obj):
        request = self.context.get('request')
        logo_url = obj.branch.edu_center.logo.url if obj.branch.edu_center.logo else None
        if request and logo_url:
            return request.build_absolute_uri(logo_url)
        return logo_url
