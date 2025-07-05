import random
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView

from django.db.models import Count, OuterRef, Exists, Value, BooleanField
from .models import TestAttempt, UserLevelProgress, Pack
from .serializers import (
    QuestionSerializer, TestSubmissionSerializer,
    TestResultSerializer, LevelProgressSerializer,
    PackSerializer
)
from main.models import Level

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
    list:    GET /api/levels/{level_id}/packs/
    retrieve:GET /api/levels/{level_id}/packs/{pk}/
    questions: GET  .../packs/{pk}/questions/
    submit:    POST .../packs/{pk}/questions/submit/
    """
    serializer_class = PackSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        level = get_object_or_404(Level, pk=self.kwargs['level_id'])
        qs = Pack.objects.filter(level=level).annotate(
            question_count=Count('questions')
        )
        if self.request.user.is_authenticated:
            attempted = TestAttempt.objects.filter(
                user=self.request.user,
                pack=OuterRef('pk')
            )
            qs = qs.annotate(used=Exists(attempted))
        else:
            qs = qs.annotate(used=Value(False, output_field=BooleanField()))
        return qs

    @swagger_auto_schema(
        method='get',
        operation_summary='Get 20 random questions from a pack',
        responses={200: QuestionSerializer(many=True)}
    )
    @action(
        detail=True,
        methods=['get'],
        url_path='questions',
        permission_classes=[IsAuthenticatedOrReadOnly]
    )
    def questions(self, request, level_id=None, pk=None):
        pack = get_object_or_404(Pack, pk=pk, level_id=level_id)
        items = list(pack.questions.prefetch_related('answers'))
        sample_qs = random.sample(items, min(len(items), QUESTIONS_PER_PACK))
        return Response(QuestionSerializer(sample_qs, many=True).data)

    @swagger_auto_schema(
        method='post',
        operation_summary='Submit answers for a pack test',
        operation_description='Accepts an array of {question: ID, answer: ID}, scores it, saves a TestAttempt, and updates UserLevelProgress.',
        request_body=TestSubmissionSerializer,
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
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        data = ser.validated_data['answers']
        questions = {q.id: q for q in pack.questions.prefetch_related('answers')}
        correct = 0
        for item in data:
            q = questions.get(item['question'])
            if not q:
                continue
            chosen = next((a for a in q.answers.all() if a.id == item['answer']), None)
            if chosen and chosen.correct:
                correct += 1

        total = len(data)
        percent = (correct / total) * 100 if total else 0

        attempt = TestAttempt.objects.create(
            user=request.user,
            pack=pack,
            correct_count=correct,
            total_questions=total,
            percent=percent
        )

        prog, _ = UserLevelProgress.objects.get_or_create(
            user=request.user,
            level=pack.level
        )
        prog.record(attempt)

        return Response(
            TestResultSerializer(attempt, context={'request': request}).data,
            status=status.HTTP_200_OK
        )


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
