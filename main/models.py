from django_quill.fields import QuillField
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
    name = models.CharField(max_length=255)
    icon_class = models.CharField(
        max_length=100,
        blank=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Level(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="levels"
    )
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ("category", "name")
        ordering = ["category__name", "name"]

    def __str__(self):
        return f"{self.category.name} – {self.name}"


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

    full_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)
    branch = models.ForeignKey(
        "Branch", on_delete=models.CASCADE, related_name="teachers"
    )

    def __str__(self):
        return f"Teacher - {self.full_name} - {self.branch}"


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
        Teacher, on_delete=models.SET_NULL, related_name="courses", null=True
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
    # Har bir til uchun alohida ustun
    image_uz = models.ImageField(upload_to="banners/uz/")
    image_en = models.ImageField(upload_to="banners/en/")
    image_ru = models.ImageField(upload_to="banners/ru/")

    def __str__(self):
        return f"Banner #{self.pk}"



class Enrollment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING",   "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELED = "CANCELED",  "Canceled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )
    course = models.ForeignKey(
        "main.Course",
        on_delete=models.CASCADE,
        related_name="enrollments"
    )
    applied_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )
    cancelled_reason = models.TextField(
        blank=True,
        null=True,
        help_text="If status=CANCELED, give a reason"
    )

    class Meta:
        unique_together = ("user", "course")
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.user} → {self.course.name} ({self.status})"


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


