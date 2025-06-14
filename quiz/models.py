from django.db import models
from django_quill.fields import QuillField
from django.conf import settings

from main.models import Level


class Quiz(models.Model):
    class QuizType(models.TextChoices):
        MULTIPLE_CHOICE = "MC", "Multiple Choice"
        LISTENING = "LI", "Listening"
        READING = "RE", "Reading"

    name = models.CharField(max_length=255)
    description = QuillField(blank=True, null=True)
    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name="quizzes"
    )
    type = models.CharField(
        max_length=2,
        choices=QuizType.choices,
        default=QuizType.MULTIPLE_CHOICE
    )
    audio = models.FileField(
        upload_to="quizzes/audio/",
        blank=True, null=True,
        help_text="Only for Listening quizzes"
    )
    image = models.ImageField(
        upload_to="quizzes/images/",
        blank=True, null=True,
        help_text="Only for Reading quizzes"
    )

    class Meta:
        ordering = ["level", "name"]
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="questions"
    )
    text = models.TextField()
    position = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["quiz", "position"]

    def __str__(self):
        return f"Q{self.position}: {self.text[:30]}…"


class Answer(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="answers"
    )
    text = models.TextField()
    correct = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["question", "position"]

    def __str__(self):
        mark = "✔" if self.correct else "✘"
        return f"{mark} {self.text[:30]}…"


class UserQuizResult(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_results"
    )
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="results"
    )
    correct_count = models.PositiveIntegerField()
    total_questions = models.PositiveIntegerField()
    taken_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-taken_at"]
        unique_together = ("user", "quiz") 

    @property
    def percent(self):
        if self.total_questions:
            return (self.correct_count / self.total_questions) * 100
        return 0


class UserLevelProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="level_progress"
    )
    level = models.ForeignKey(
        Level, on_delete=models.CASCADE, related_name="user_progress"
    )
    passed_quizzes = models.PositiveIntegerField(default=0)
    total_quizzes = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "level")
        ordering = ["user", "level"]

    @property
    def percent_passed(self):
        if self.total_quizzes:
            return (self.passed_quizzes / self.total_quizzes) * 100
        return 0

    def record_result(self, result: UserQuizResult):
        """
        Bitta quiz yakunlanganda chaqiriladi:
        - total_quizzes +1
        - agar result.percent >= 50: passed_quizzes +1
        """
        self.total_quizzes += 1
        if result.percent >= 50:
            self.passed_quizzes += 1
        self.save()
