from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        Group, Permission, PermissionsMixin)
from django.core.exceptions import ValidationError
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, username=None, full_name=None, password=None, **extra_fields):
        role = extra_fields.get("role", "STUDENT")
        if role in ["SUPERUSER", "EDU_CENTER", "BRANCH"] and not username:
            raise ValueError(
                "SUPERUSER, EDU_CENTER, and BRANCH users must have a username."
            )
        if not full_name:
            raise ValueError("The full name must be set.")
        user = self.model(username=username, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, full_name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "SUPERUSER")
        return self.create_user(username, full_name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("SUPERUSER", "Superuser"),
        ("EDU_CENTER", "Education Center"),
        ("BRANCH", "Branch Admin"),
        ("STUDENT", "Student"),
        ("ACCOUNTANT", "Accountant"),
    ]

    GENDER_CHOICES = [
        ("MALE", "Male"),
        ("FEMALE", "Female"),
        ("OTHER", "Other"),
    ]

    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    full_name = models.CharField(max_length=255)
    telegram_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    birth_date = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=10, choices=GENDER_CHOICES, blank=True, null=True
    )
    country = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="STUDENT")
    is_verified = models.BooleanField(default=False)
    is_partner = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    groups = models.ManyToManyField(Group, related_name="custom_user_set", blank=True)
    user_permissions = models.ManyToManyField(
        Permission, related_name="custom_user_permissions_set", blank=True
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["full_name"]

    def __str__(self):
        return self.username or self.full_name

    def clean(self):
        super().clean()
        admin_roles = ["SUPERUSER", "EDU_CENTER", "BRANCH"]
        if self.role in admin_roles:
            if not self.username:
                raise ValidationError(f"{self.role} users must have a username.")
        else:
            if not self.telegram_id and not self.phone_number:
                raise ValidationError(
                    "Either telegram_id or phone_number is required for this role."
                )

    def save(self, *args, **kwargs):
        if not self.username and self.role not in ["SUPERUSER", "EDU_CENTER", "BRANCH"]:
            self.username = self.telegram_id or self.phone_number

        if self.role != "EDU_CENTER":
            self.is_verified = False
            self.is_partner = False

        self.full_clean()
        super().save(*args, **kwargs)
