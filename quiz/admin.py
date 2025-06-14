from django.contrib import admin
from .models import (
    Quiz,
    Question,
    Answer,
    UserQuizResult,
    UserLevelProgress,
)


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1
    fields = ("text", "correct", "position")


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ("position", "text")
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "type")
    list_filter = ("type", "level")
    search_fields = ("name",)
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("quiz", "position", "short_text")
    list_filter = ("quiz",)
    search_fields = ("text",)
    inlines = [AnswerInline]

    def short_text(self, obj):
        return obj.text[:50] + ("…" if len(obj.text) > 50 else "")
    short_text.short_description = "Question Text"


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("question", "short_text", "correct", "position")
    list_filter = ("correct",)
    search_fields = ("text",)

    def short_text(self, obj):
        return obj.text[:50] + ("…" if len(obj.text) > 50 else "")
    short_text.short_description = "Answer Text"


@admin.register(UserQuizResult)
class UserQuizResultAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "quiz",
        "correct_count",
        "total_questions",
        "percent",
        "taken_at",
    )
    list_filter = ("quiz", "user")
    readonly_fields = ("percent", "taken_at")
    date_hierarchy = "taken_at"


@admin.register(UserLevelProgress)
class UserLevelProgressAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "level",
        "passed_quizzes",
        "total_quizzes",
        "percent_passed",
        "last_updated",
    )
    list_filter = ("level", "user")
    readonly_fields = ("percent_passed", "last_updated")
    date_hierarchy = "last_updated"
