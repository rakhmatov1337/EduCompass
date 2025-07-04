import random

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import TestAttempt, UserLevelProgress
from .serializers import (
    QuestionSerializer, TestSubmissionSerializer,
    TestResultSerializer, LevelProgressSerializer
)
from main.models import Level

QUESTIONS_PER_TEST = 20


class LevelQuestionView(generics.ListAPIView):
    """
    GET /api/levels/{level_id}/questions/  —  random 20 savolni qaytaradi
    """
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_summary="Get random questions for a level",
        operation_description="Returns up to 20 random questions for the specified level.",
        responses={200: QuestionSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        level = get_object_or_404(Level, pk=self.kwargs["level_id"])
        qs = list(level.questions.prefetch_related("answers").all())
        return random.sample(qs, min(len(qs), QUESTIONS_PER_TEST))


class LevelTestView(generics.GenericAPIView):
    """
    POST /api/levels/{level_id}/submit/  — test javoblarini qabul qiladi va natija beradi
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TestSubmissionSerializer

    @swagger_auto_schema(
        operation_summary="Submit answers for a level test",
        operation_description="Submit answers for a test. Returns the result and updates user progress.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'answers': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'question': openapi.Schema(type=openapi.TYPE_INTEGER, description='Question ID'),
                            'answer': openapi.Schema(type=openapi.TYPE_INTEGER, description='Answer ID'),
                        },
                        required=['question', 'answer'],
                    ),
                    example=[
                        {"question": 12, "answer": 45},
                        {"question": 13, "answer": 47},
                        {"question": 14, "answer": 52}
                    ]
                )
            },
            required=['answers'],
            example={
                "answers": [
                    {"question": 12, "answer": 45},
                    {"question": 13, "answer": 47},
                    {"question": 14, "answer": 52}
                ]
            }
        ),
        responses={200: TestResultSerializer}
    )
    def post(self, request, level_id):
        level = get_object_or_404(Level, pk=level_id)
        sub_ser = self.get_serializer(data=request.data)
        sub_ser.is_valid(raise_exception=True)

        answers = sub_ser.validated_data["answers"]
        questions = {q.id: q for q in level.questions.prefetch_related("answers").all()}
        correct = 0
        for item in answers:
            q = questions.get(item.get("question"))
            if not q:
                continue
            chosen = next((a for a in q.answers.all()
                          if a.id == item.get("answer")), None)
            if chosen and chosen.correct:
                correct += 1

        total = len(answers)
        pct = (correct / total) * 100 if total else 0

        attempt = TestAttempt.objects.create(
            user=request.user,
            level=level,
            correct_count=correct,
            total_questions=total,
            percent=pct
        )

        prog, _ = UserLevelProgress.objects.get_or_create(
            user=request.user, level=level)
        prog.record(attempt)

        out = TestResultSerializer(attempt, context={"request": request})
        return Response(out.data, status=status.HTTP_200_OK)


class LevelProgressView(generics.RetrieveAPIView):
    """
    GET /api/levels/{level_id}/progress/ — foydalanuvchi progress va foiz
    """
    permission_classes = [IsAuthenticated]
    serializer_class = LevelProgressSerializer

    @swagger_auto_schema(
        operation_summary="Get user progress for a level",
        operation_description="Returns the user's progress and percentage for the specified level.",
        responses={200: LevelProgressSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        level = get_object_or_404(Level, pk=self.kwargs["level_id"])
        prog, _ = UserLevelProgress.objects.get_or_create(
            user=self.request.user, level=level)
        return prog


class QuizFilterSchemaView(APIView):

    @swagger_auto_schema(
        operation_summary="Quiz filter schema",
        operation_description="Returns available filters for quizzes.",
        responses={200: openapi.Response(
            description="Filter schema",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "level": openapi.Schema(type=openapi.TYPE_STRING),
                    "level_name": openapi.Schema(type=openapi.TYPE_STRING),
                    "type": openapi.Schema(type=openapi.TYPE_STRING),
                    "search": openapi.Schema(type=openapi.TYPE_STRING),
                    "ordering": openapi.Schema(type=openapi.TYPE_STRING),
                    "page": openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        )}
    )
    def get(self, request):
        return Response({
            "level":       "integer: filter by level ID",
            "level_name":  "string: case-insensitive exact match on level name",
            "type":        "string: quiz type code (e.g. 'MC' | 'LI' | 'RE')",
            "search":      "string: search in quiz name",
            "ordering":    "string: comma-separated ordering fields, e.g. 'name' or '-level__name'",
            "page":        "integer: pagination page number",
        })
