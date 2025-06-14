from rest_framework import serializers
from .models import (
    Quiz, Question, Answer,
    UserQuizResult, UserLevelProgress
)


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text', 'correct', 'position']


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'quiz', 'position', 'text', 'answers']


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            'id', 'name', 'description', 'level',
            'type', 'audio', 'image', 'questions'
        ]
        read_only_fields = ['questions']


class SubmissionAnswerSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    answer = serializers.IntegerField()


class QuizSubmissionSerializer(serializers.Serializer):
    answers = SubmissionAnswerSerializer(many=True)


class UserQuizResultSerializer(serializers.ModelSerializer):
    percent = serializers.FloatField(read_only=True)

    class Meta:
        model = UserQuizResult
        fields = [
            'id', 'user', 'quiz',
            'correct_count', 'total_questions',
            'percent', 'taken_at'
        ]
        read_only_fields = ['percent', 'taken_at', 'user']


class UserLevelProgressSerializer(serializers.ModelSerializer):
    percent_passed = serializers.FloatField(read_only=True)

    class Meta:
        model = UserLevelProgress
        fields = [
            'id', 'user', 'level',
            'passed_quizzes', 'total_quizzes',
            'percent_passed', 'last_updated'
        ]
        read_only_fields = ['percent_passed', 'last_updated', 'user']
