from django.contrib import admin
from .models import Pack, Question, Answer, TestAttempt, UserLevelProgress


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Pack)
class PackAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "level", "description")
    list_filter = ("level",)
    search_fields = ("title", "description")
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "pack", "position", "text")
    list_filter = ("pack",)
    search_fields = ("text",)
    inlines = [AnswerInline]
    ordering = ("pack", "position")


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "text", "correct")
    list_filter = ("correct", "question__pack")
    search_fields = ("text",)


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "pack", "correct_count", "total_questions", "percent", "taken_at")
    list_filter = ("pack", "user")
    search_fields = ("user__username", "pack__title")
    readonly_fields = ("taken_at",)


@admin.register(UserLevelProgress)
class UserLevelProgressAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "level", "total_tests", "passed_tests", "percent")
    list_filter = ("level", "user")
    search_fields = ("user__username", "level__name")
    readonly_fields = ("user", "level")