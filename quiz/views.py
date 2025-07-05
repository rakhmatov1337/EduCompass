import random
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView

from .models import TestAttempt, UserLevelProgress, Pack
from .serializers import (
    QuestionSerializer, TestSubmissionSerializer,
    TestResultSerializer, LevelProgressSerializer,
    PackSerializer
)
from main.models import Level
from django.db.models import Count

QUESTIONS_PER_TEST = 20
QUESTIONS_PER_PACK = 20


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


class PackViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ReadOnly viewset for Packs under a Level.

    list:
    GET /api/levels/{level_id}/packs/

    retrieve:
    GET /api/levels/{level_id}/packs/{pk}/

    questions:
    GET /api/levels/{level_id}/packs/{pk}/questions/

    submit:
    POST /api/levels/{level_id}/packs/{pk}/submit/
    """
    serializer_class = PackSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        # Prevent errors during schema generation (swagger_fake_view)
        if getattr(self, 'swagger_fake_view', False):
            return Pack.objects.none()

        level_id = self.kwargs.get('level_id')
        level = get_object_or_404(Level, pk=level_id)
        return Pack.objects.filter(level=level).annotate(
            question_count=Count('questions')
        )

    @swagger_auto_schema(
        method='get',
        operation_summary='Get 20 random questions from a pack',
        operation_description='Returns up to 20 randomly selected questions for the specified pack.',
        responses={200: QuestionSerializer(many=True)}
    )
    @action(detail=True, methods=['get'], url_path='questions', permission_classes=[IsAuthenticatedOrReadOnly])
    def questions(self, request, level_id=None, pk=None):
        pack = get_object_or_404(Pack, pk=pk, level_id=level_id)
        questions = list(pack.questions.prefetch_related('answers'))
        selected = random.sample(questions, min(len(questions), QUESTIONS_PER_PACK))
        serializer = QuestionSerializer(selected, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        method='post',
        operation_summary='Submit answers for a pack test',
        operation_description='Accepts an array of {"question": id, "answer": id} objects, computes score, saves attempt, and updates user level progress.',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'answers': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description='List of question-answer mappings',
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'question': openapi.Schema(type=openapi.TYPE_INTEGER, description='Question ID'),
                            'answer': openapi.Schema(type=openapi.TYPE_INTEGER, description='Answer ID'),
                        },
                        required=['question', 'answer']
                    ),
                    example=[
                        {'question': 10, 'answer': 42},
                        {'question': 11, 'answer': 45},
                    ]
                )
            },
            required=['answers']
        ),
        responses={200: TestResultSerializer}
    )
    @action(
        detail=True,
        methods=['post'],
        url_path='questions/submit',
        permission_classes=[IsAuthenticated],
        serializer_class=TestSubmissionSerializer
    )
    def submit(self, request, level_id=None, pk=None):
        pack = get_object_or_404(Pack, pk=pk, level_id=level_id)
        sub_ser = self.get_serializer(data=request.data)
        sub_ser.is_valid(raise_exception=True)

        answers_data = sub_ser.validated_data['answers']
        # map questions for fast lookup
        questions_map = {q.id: q for q in pack.questions.prefetch_related('answers')}
        correct = 0
        for item in answers_data:
            q = questions_map.get(item.get('question'))
            if not q:
                continue
            chosen = next((a for a in q.answers.all()
                          if a.id == item.get('answer')), None)
            if chosen and chosen.correct:
                correct += 1

        total = len(answers_data)
        percent = (correct / total) * 100 if total else 0

        attempt = TestAttempt.objects.create(
            user=request.user,
            pack=pack,
            correct_count=correct,
            total_questions=total,
            percent=percent
        )

        progress, _ = UserLevelProgress.objects.get_or_create(
            user=request.user,
            level=pack.level
        )
        progress.record(attempt)

        out = TestResultSerializer(attempt, context={'request': request})
        return Response(out.data, status=status.HTTP_200_OK)


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
