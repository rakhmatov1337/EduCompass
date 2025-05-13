from django.conf import settings
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.validators import RegexValidator
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.validators import FileExtensionValidator


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
        MONDAY = 'MONDAY', 'Monday'
        TUESDAY = 'TUESDAY', 'Tuesday'
        WEDNESDAY = 'WEDNESDAY', 'Wednesday'
        THURSDAY = 'THURSDAY', 'Thursday'
        FRIDAY = 'FRIDAY', 'Friday'
        SATURDAY = 'SATURDAY', 'Saturday'
        SUNDAY = 'SUNDAY', 'Sunday'

    name = models.CharField(max_length=10, choices=DayChoices.choices)

    def __str__(self):
        return self.get_name_display()


class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    liked_at = models.DateTimeField(auto_now_add=True)


class View(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    viewed_at = models.DateTimeField(auto_now_add=True)


class EducationCenter(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'EDU_CENTER'},
        related_name='education_center', null=True
    )
    description = models.TextField(blank=True)
    country = models.CharField(max_length=255)
    region = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+998911234567'. Up to 12 digits allowed.")
    phone_number = models.CharField(
        validators=[phone_regex], max_length=15, blank=True, null=True)
    edu_type = models.ManyToManyField(
        EduType, related_name='education_centers')
    categories = models.ManyToManyField(
        Category, related_name='education_centers', blank=True)
    logo = models.ImageField(upload_to='education_centers/logos/', blank=True, null=True,
                             validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])])
    cover = models.ImageField(upload_to='education_centers/banners/', blank=True, null=True,
                              validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])])
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
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
    ]

    name = models.CharField(max_length=255)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)
    branch = models.ForeignKey(
        'Branch', on_delete=models.CASCADE, related_name='teachers')

    def __str__(self):
        return f"Teacher - {self.name} - {self.branch}"


class Branch(models.Model):
    name = models.CharField(max_length=255)
    edu_center = models.ForeignKey(
        EducationCenter, on_delete=models.CASCADE, related_name='branches')
    country = models.CharField(max_length=255)
    region = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    admins = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        limit_choices_to={'role': 'BRANCH'},
        related_name='branches'
    )

    def __str__(self):
        return f"{self.name} ({self.edu_center.name})"


class Event(models.Model):
    name = models.CharField(max_length=255)
    picture = models.ImageField(upload_to='events/')
    edu_center = models.ForeignKey(
        EducationCenter, on_delete=models.CASCADE, related_name='events')
    date = models.DateField()
    time = models.TimeField()
    description = models.TextField()
    link = models.URLField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.edu_center.name}"


class Course(models.Model):
    name = models.CharField(max_length=255)
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name='courses')
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='courses')
    days = models.ManyToManyField(Day, related_name='courses')
    level = models.ForeignKey(
        Level, on_delete=models.CASCADE, related_name='courses')
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    booked_places = models.IntegerField(default=0)
    total_places = models.IntegerField()
    teacher = models.ForeignKey(
        Teacher, on_delete=models.CASCADE, related_name='courses')
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
        ordering = ['start_date']
        unique_together = ('name', 'branch')


class Banner(models.Model):
    LANGUAGE_CHOICES = [
        ('uz', 'Uzbek'),
        ('en', 'English'),
        ('ru', 'Russian'),
    ]

    image = models.ImageField(upload_to='banners/')
    language_code = models.CharField(
        max_length=10, choices=LANGUAGE_CHOICES, default='uz')

    def __str__(self):
        return f"Banner ({self.language_code})"
