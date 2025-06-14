from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.views import APIView

from api.paginations import DefaultPagination
from .models import Quiz, Question, Answer, UserQuizResult, UserLevelProgress
from .serializers import (
    QuizSerializer, QuestionSerializer, AnswerSerializer,
    QuizSubmissionSerializer, UserQuizResultSerializer,
    UserLevelProgressSerializer
)


class QuizViewSet(viewsets.ModelViewSet):
    """
    List / Retrieve / Create / Update / Destroy for Quiz.
    N+1-free: prefetches questions + answers, select_related level.
    Supports filtering by level and type, searching by name, and ordering.
    """
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = DefaultPagination

    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['level', 'type']
    search_fields = ['name']
    ordering_fields = ['level__name', 'name']
    ordering = ['level__name', 'name']

    def get_queryset(self):
        # select the FK 'level', prefetch all questions and their answers in two queries
        return (
            Quiz.objects
                .all()
                .select_related('level')
                .prefetch_related('questions__answers')
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def submit(self, request, pk=None):
        quiz = self.get_object()
        sub_ser = QuizSubmissionSerializer(data=request.data)
        sub_ser.is_valid(raise_exception=True)

        # Calculate score
        total_questions = quiz.questions.count()
        correct_count = 0
        # Because we prefetched questions__answers above, these lookups hit the cache
        for item in sub_ser.validated_data['answers']:
            try:
                q = next(q for q in quiz.questions.all() if q.id == item['question'])
                a = next(a for a in q.answers.all() if a.id == item['answer'])
                if a.correct:
                    correct_count += 1
            except StopIteration:
                continue

        # Save result
        result_obj, _ = UserQuizResult.objects.update_or_create(
            user=request.user,
            quiz=quiz,
            defaults={
                'correct_count': total_questions and correct_count or 0,
                'total_questions': total_questions
            }
        )

        # Update level progress
        progress_obj, _ = UserLevelProgress.objects.get_or_create(
            user=request.user,
            level=quiz.level,
            defaults={'passed_quizzes': 0, 'total_quizzes': 0}
        )
        progress_obj.record_result(result_obj)

        out_ser = UserQuizResultSerializer(result_obj, context={'request': request})
        return Response(out_ser.data, status=status.HTTP_200_OK)


class QuestionViewSet(viewsets.ModelViewSet):
    """
    CRUD for Questions.
    N+1-free: select_related quiz, prefetch answers.
    Supports filtering by quiz, searching by text, ordering by position.
    """
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['quiz']
    search_fields = ['text']
    ordering_fields = ['position']
    ordering = ['position']

    def get_queryset(self):
        return (
            Question.objects
            .all()
            .select_related('quiz')
            .prefetch_related('answers')
        )


class AnswerViewSet(viewsets.ModelViewSet):
    """
    CRUD for Answers.
    N+1-free: select_related question.
    Supports filtering by question, searching by text, ordering by position.
    """
    serializer_class = AnswerSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['question']
    search_fields = ['text']
    ordering_fields = ['position']
    ordering = ['position']

    def get_queryset(self):
        return Answer.objects.all().select_related('question')


class UserQuizResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only listing of the current user's quiz results.
    N+1-free: select_related quiz + level.
    Can optionally be filtered by quiz.
    """
    serializer_class = UserQuizResultSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['quiz']

    def get_queryset(self):
        return (
            UserQuizResult.objects
            .filter(user=self.request.user)
            .select_related('quiz', 'quiz__level')
        )


class UserLevelProgressViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only listing of the current user's level progress.
    N+1-free: select_related level.
    """
    serializer_class = UserLevelProgressSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['level']

    def get_queryset(self):
        return (
            UserLevelProgress.objects
            .filter(user=self.request.user)
            .select_related('level')
        )


class QuizFilterSchemaView(APIView):

    def get(self, request):
        return Response({
            "level":       "integer: filter by level ID",
            "level_name":  "string: case-insensitive exact match on level name",
            "type":        "string: quiz type code (e.g. 'MC' | 'LI' | 'RE')",
            "search":      "string: search in quiz name",
            "ordering":    "string: comma-separated ordering fields, e.g. 'name' or '-level__name'",
            "page":        "integer: pagination page number",
        })
