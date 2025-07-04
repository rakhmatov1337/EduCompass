from django.db import models
from django.conf import settings
from main.models import Level


class Question(models.Model):
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    position = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["level", "position"]

    def __str__(self):
        return f"{self.level.name} Q{self.position}"


class Answer(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="answers")
    text = models.CharField(max_length=255)
    correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["-correct", "id"]

    def __str__(self):
        return f"{'✔' if self.correct else '✘'} {self.text[:30]}"


class TestAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    correct_count = models.PositiveIntegerField()
    total_questions = models.PositiveIntegerField()
    percent = models.FloatField()
    taken_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-taken_at"]


class UserLevelProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, related_name="progress")
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    total_tests = models.PositiveIntegerField(default=0)
    passed_tests = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "level")

    @property
    def percent(self):
        if not self.total_tests:
            return 0
        return (self.passed_tests / self.total_tests) * 100

    def record(self, attempt: TestAttempt):
        self.total_tests += 1
        if attempt.percent >= 50:
            self.passed_tests += 1
        self.save()
