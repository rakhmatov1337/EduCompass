from django.contrib import admin

from .models import (Branch, Category, Course, Day, EducationCenter, EduType,
                     Enrollment, Event, Level, Teacher, Unit, QuizType, Quiz, Question, Answer)

# Register your models here.

admin.site.register(EduType)
admin.site.register(Category)
admin.site.register(Day)
admin.site.register(Teacher)
admin.site.register(EducationCenter)
admin.site.register(Branch)
admin.site.register(Course)
admin.site.register(Level)
admin.site.register(Event)
admin.site.register(Enrollment)


class QuizInline(admin.TabularInline):
    model = Quiz
    extra = 0
    fields = ('name', 'quiz_type', 'points')
    show_change_link = True


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ('position', 'text')
    show_change_link = True


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2
    fields = ('text', 'correct')
    show_change_link = False


# Quiz

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('number', 'title', 'created_at')
    search_fields = ('title',)
    ordering = ('number',)
    inlines = [QuizInline]


@admin.register(QuizType)
class QuizTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit', 'quiz_type', 'points', 'show_select')
    list_filter = ('unit', 'quiz_type', 'show_select')
    search_fields = ('name', 'topic')
    ordering = ('unit__number', 'quiz_type__name', 'name')
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text_short', 'quiz', 'position')
    list_filter = ('quiz',)
    search_fields = ('text',)
    ordering = ('quiz__id', 'position')
    inlines = [AnswerInline]

    def text_short(self, obj):
        return (obj.text[:50] + '…') if len(obj.text) > 50 else obj.text
    text_short.short_description = 'Question'


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text_short', 'question', 'correct')
    list_filter = ('correct', 'question')
    search_fields = ('text',)
    ordering = ('question__id',)

    def text_short(self, obj):
        return (obj.text[:50] + '…') if len(obj.text) > 50 else obj.text
    text_short.short_description = 'Answer'
