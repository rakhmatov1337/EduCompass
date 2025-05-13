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
    display_name = serializers.CharField(source='get_name_display', read_only=True)

    class Meta:
        model = Day
        fields = ['id', 'name', 'display_name']
        read_only_fields = ['id', 'display_name']


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ['id', 'name', 'gender', 'branch']


class BranchMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['id', 'name', 'city']

class TeacherMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ['id', 'name', 'gender']


class CourseSerializer(serializers.ModelSerializer):
    final_price = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    available_places = serializers.IntegerField(read_only=True)

    branch = BranchMiniSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    level = LevelSerializer(read_only=True)
    teacher = TeacherMiniSerializer(read_only=True)
    days = DaySerializer(read_only=True, many=True)

    class Meta:
        model = Course
        exclude = ['is_archived']
