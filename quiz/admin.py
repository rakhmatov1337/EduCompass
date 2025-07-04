from django.contrib import admin
from .models import Question, Answer, TestAttempt, UserLevelProgress


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "level", "position", "text")
    list_filter = ("level",)
    search_fields = ("text",)
    inlines = [AnswerInline]
    ordering = ("level", "position")


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "text", "correct")
    list_filter = ("correct", "question__level")
    search_fields = ("text",)


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "level", "correct_count", "total_questions", "percent", "taken_at")
    list_filter = ("level", "user")
    search_fields = ("user__username", "level__name")
    readonly_fields = ("taken_at",)


@admin.register(UserLevelProgress)
class UserLevelProgressAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "level", "total_tests", "passed_tests", "percent")
    list_filter = ("level", "user")
    search_fields = ("user__username", "level__name")
    readonly_fields = ("id", "user", "level", "total_tests", "passed_tests", "percent")