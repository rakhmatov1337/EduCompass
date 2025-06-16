from django_quill.fields import QuillField  # assuming this import
from django_quill.fields import QuillField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.contrib.contenttypes.fields import (GenericForeignKey,
                                                GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models
from django.utils import timezone


class EduType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Level(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Day(models.Model):
    class DayChoices(models.TextChoices):
        MONDAY = "MONDAY", "Monday"
        TUESDAY = "TUESDAY", "Tuesday"
        WEDNESDAY = "WEDNESDAY", "Wednesday"
        THURSDAY = "THURSDAY", "Thursday"
        FRIDAY = "FRIDAY", "Friday"
        SATURDAY = "SATURDAY", "Saturday"
        SUNDAY = "SUNDAY", "Sunday"

    name = models.CharField(max_length=10, choices=DayChoices.choices)

    def __str__(self):
        return self.get_name_display()


class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    liked_at = models.DateTimeField(auto_now_add=True)


class View(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    viewed_at = models.DateTimeField(auto_now_add=True)


class EducationCenter(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "EDU_CENTER"},
        related_name="education_center",
        null=True,
    )
    description = models.TextField(blank=True)
    country = models.CharField(max_length=255)
    region = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message="Phone number must be entered in the format: '+998911234567'. Up to 12 digits allowed.",
    )
    phone_number = models.CharField(
        validators=[phone_regex], max_length=15, blank=True, null=True
    )
    edu_type = models.ManyToManyField(EduType, related_name="education_centers")
    categories = models.ManyToManyField(
        Category, related_name="education_centers", blank=True
    )
    logo = models.ImageField(
        upload_to="education_centers/logos/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"])
        ],
    )
    cover = models.ImageField(
        upload_to="education_centers/banners/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"])
        ],
    )
    instagram_link = models.URLField(max_length=255, blank=True, null=True)
    telegram_link = models.URLField(max_length=255, blank=True, null=True)
    facebook_link = models.URLField(max_length=255, blank=True, null=True)
    website_link = models.URLField(max_length=255, blank=True, null=True)
    active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    likes = GenericRelation(Like)
    views = GenericRelation(View)

    def __str__(self):
        return f"{self.name}"


class Teacher(models.Model):
    GENDER_CHOICES = [
        ("MALE", "Male"),
        ("FEMALE", "Female"),
    ]

    name = models.CharField(max_length=255)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)
    branch = models.ForeignKey(
        "Branch", on_delete=models.CASCADE, related_name="teachers"
    )

    def __str__(self):
        return f"Teacher - {self.name} - {self.branch}"


class Branch(models.Model):
    name = models.CharField(max_length=255)
    edu_center = models.ForeignKey(
        EducationCenter, on_delete=models.CASCADE, related_name="branches"
    )

    latitude = models.DecimalField(
        max_digits=10, decimal_places=7, blank=True, null=True
    )
    longitude = models.DecimalField(
        max_digits=11, decimal_places=7, blank=True, null=True
    )

    phone_regex = RegexValidator(
        regex=r"^\+?998\d{9}$",
        message="Telefon raqam quyidagi formatda bo‘lishi kerak: +998901234567",
    )
    phone_number = models.CharField(
        validators=[phone_regex], max_length=15, blank=True, null=True
    )

    work_time = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Ish vaqti, masalan: 09:00-18:00",
    )
    telegram_link = models.URLField(max_length=255, blank=True, null=True)

    admins = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        limit_choices_to={"role": "BRANCH"},
        related_name="branches",
    )

    def __str__(self):
        return f"{self.name} ({self.edu_center.name})"


class Event(models.Model):
    REQUIREMENT_CHOICES = [
        ("FREE", "Bepul"),
        ("PAID", "Pullik"),
    ]

    name = models.CharField(max_length=255)
    picture = models.ImageField(upload_to="events/")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="events")
    edu_center = models.ForeignKey(
        EducationCenter, on_delete=models.CASCADE, related_name="events"
    )
    categories = models.ManyToManyField(Category, related_name="events", blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    requirements = models.CharField(max_length=10, choices=REQUIREMENT_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    description = models.TextField()
    link = models.URLField(max_length=255, blank=True, null=True)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.edu_center.name}"


class Course(models.Model):
    name = models.CharField(max_length=255)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="courses")
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="courses"
    )
    days = models.ManyToManyField(Day, related_name="courses")
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="courses")
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    booked_places = models.IntegerField(default=0)
    total_places = models.IntegerField()
    teacher = models.ForeignKey(
        Teacher, on_delete=models.CASCADE, related_name="courses"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_time = models.TimeField()
    end_time = models.TimeField()
    intensive = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.branch.name} / {self.branch.edu_center.name})"

    @property
    def final_price(self):
        return max(self.price - self.discount, 0)

    @property
    def available_places(self):
        return max(self.total_places - self.booked_places, 0)

    class Meta:
        ordering = ["start_date"]
        unique_together = ("name", "branch")


class Banner(models.Model):
    LANGUAGE_CHOICES = [
        ("uz", "Uzbek"),
        ("en", "English"),
        ("ru", "Russian"),
    ]

    image = models.ImageField(upload_to="banners/")
    language_code = models.CharField(
        max_length=10, choices=LANGUAGE_CHOICES, default="uz"
    )

    def __str__(self):
        return f"Banner ({self.language_code})"


class Enrollment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments"
    )
    course = models.ForeignKey(
        "main.Course", on_delete=models.CASCADE, related_name="enrollments"
    )
    applied_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "course")
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.user} → {self.course.name}"


# Quiz model


class QuizType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Quiz Type"
        verbose_name_plural = "Quiz Types"

    def __str__(self):
        return self.name


class Unit(models.Model):
    number = models.PositiveIntegerField(
        unique=True,
        help_text="Sequential number (e.g. 1,2,3…)"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['number']
        verbose_name = "Unit"
        verbose_name_plural = "Units"

    def __str__(self):
        return f"Unit {self.number}: {self.title}"


def get_last_unit():
    last = Unit.objects.order_by('number').last()
    return last.id if last else None


class Quiz(models.Model):
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name="quizzes",
        blank=True,
        null=True,
        default=get_last_unit,
    )
    quiz_type = models.ForeignKey(QuizType, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    topic = models.CharField(max_length=70, blank=True)
    description = QuillField(blank=True, null=True)
    points = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    show_select = models.BooleanField(default=True)
    audio = models.FileField(upload_to='audio/', blank=True, null=True)
    image = models.ImageField(upload_to='quiz_pics/', blank=True, null=True)

    class Meta:
        verbose_name_plural = "Quizzes"
        ordering = ['unit__number', 'quiz_type__name', 'name']
        unique_together = (('unit', 'name'),)

    def __str__(self):
        unit_num = self.unit.number if self.unit else "?"
        return f"{self.name} (Unit {unit_num})"

    @property
    def question_list(self):
        """Return all questions related to this quiz."""
        return self.questions.all()


def get_last_quiz():
    last = Quiz.objects.order_by('pk').last()
    return last.pk if last else None


class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
        default=get_last_quiz,
        blank=True,
        null=True,
    )
    position = models.PositiveIntegerField(
        default=1,
        help_text="Ordering within the quiz."
    )
    text = models.TextField()
    end_text = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['quiz__id', 'position']
        unique_together = (('quiz', 'text'),)

        def __str__(self):
            preview = (self.text[:50] + '…') if len(self.text) > 50 else self.text
            correct = self.correct_answer
            correct_text = correct.text if correct else "No correct answer"
            return f"{preview} — {correct_text}"

    @property
    def correct_answer(self):
        return self.answer_set.filter(correct=True).first()


class Answer(models.Model):
    question = models.ForeignKey(
        'Question',
        on_delete=models.CASCADE,
        related_name='answers',
        help_text="The question this answer belongs to."
    )
    text = models.TextField(
        help_text="The answer text shown to the user."
    )
    correct = models.BooleanField(
        default=False,
        help_text="Marks whether this answer is the correct one."
    )
    position = models.PositiveIntegerField(
        default=1,
        help_text="Order of this answer among its siblings."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['question__id', 'position']
        unique_together = (('question', 'text'),)
        verbose_name = "Answer"
        verbose_name_plural = "Answers"

    def __str__(self):
        prefix = "✔" if self.correct else "✘"
        preview = (self.text[:50] + '…') if len(self.text) > 50 else self.text
        return f"{prefix} {preview}"
