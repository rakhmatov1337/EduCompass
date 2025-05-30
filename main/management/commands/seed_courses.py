from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
from faker import Faker
from main.models import Course, Category, Level, Day
from main.models import Branch, Teacher
import random


class Command(BaseCommand):
    help = 'Creates 50 fake Course records'

    def handle(self, *args, **options):
        fake = Faker()

        branches = list(Branch.objects.all())
        teachers = list(Teacher.objects.all())
        categories = list(Category.objects.all())
        levels = list(Level.objects.all())
        days = list(Day.objects.all())

        if not (branches and teachers and categories and levels and days):
            self.stdout.write(self.style.ERROR(
                "❌ Iltimos, avval branch, teacher, category, level va day obyektlarini yarating!"
            ))
            return

        for _ in range(50):
            start_time = fake.date_time_between(
                start_date='-30d', end_date='+30d')
            end_time = start_time + timedelta(hours=2)

            course = Course.objects.create(
                name=fake.sentence(nb_words=3),
                total_places=random.randint(10, 50),
                price=random.randint(100, 1000),
                branch=random.choice(branches),
                category=random.choice(categories),
                level=random.choice(levels),
                teacher=random.choice(teachers),
                start_time=start_time,
                end_time=end_time,
            )
            course.days.set(random.sample(days, k=random.randint(1, 3)))

        self.stdout.write(self.style.SUCCESS(
            "✅ 50 ta Course muvaffaqiyatli yaratildi."))
