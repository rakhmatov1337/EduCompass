# api/serializers.py
from rest_framework import serializers
from .models import Question, Answer, TestAttempt, UserLevelProgress


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ["id", "text"]


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "text", "answers"]


class TestSubmissionSerializer(serializers.Serializer):
    # client yuboradi: question ID va tanlangan answer ID
    answers = serializers.ListSerializer(
        child=serializers.DictField(child=serializers.IntegerField()),
        allow_empty=False
    )


class TestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestAttempt
        fields = ["id", "level", "correct_count",
                  "total_questions", "percent", "taken_at"]


class LevelProgressSerializer(serializers.ModelSerializer):
    percent = serializers.FloatField(read_only=True)

    class Meta:
        model = UserLevelProgress
        fields = ["level", "total_tests", "passed_tests", "percent"]
