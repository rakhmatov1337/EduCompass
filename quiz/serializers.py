from rest_framework import serializers
from .models import Question, Answer, TestAttempt, UserLevelProgress, Pack


class PackSerializer(serializers.ModelSerializer):
    question_count = serializers.IntegerField(
        source='questions.count',
        read_only=True,
        help_text="Total number of questions in this pack"
    )

    class Meta:
        model = Pack
        fields = ['id', 'title', 'description', 'question_count']



class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ["id", "text", "correct"]


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "text", "answers"]


class TestSubmissionSerializer(serializers.Serializer):
    answers = serializers.ListSerializer(
        child=serializers.DictField(child=serializers.IntegerField()),
        allow_empty=False
    )


class TestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestAttempt
        fields = ["id", "pack", "correct_count",
                  "total_questions", "percent", "taken_at"]


class LevelProgressSerializer(serializers.ModelSerializer):
    percent = serializers.FloatField(read_only=True)

    class Meta:
        model = UserLevelProgress
        fields = ["level", "total_tests", "passed_tests", "percent"]
