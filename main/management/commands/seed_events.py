from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
from faker import Faker
import random
import tempfile
import requests

from main.models import Event, EducationCenter, Branch
from django.core.files import File


class Command(BaseCommand):
    help = "Creates 50 fake Event records with random pictures"

    def handle(self, *args, **options):
        fake = Faker()

        edu_centers = list(EducationCenter.objects.all())
        branches = list(Branch.objects.all())

        if not edu_centers or not branches:
            self.stdout.write(
                self.style.ERROR(
                    "❌ Avval EducationCenter va Branch obyektlari bo'lishi kerak."
                )
            )
            return

        for _ in range(50):
            edu_center = random.choice(edu_centers)
            branch = random.choice([b for b in branches if b.edu_center == edu_center])

            # Fake rasm URL (placehold.it dan)
            image_url = fake.image_url(width=600, height=400)

            # Rasmni yuklab olish
            response = requests.get(image_url)
            if response.status_code != 200:
                continue

            image_temp = tempfile.NamedTemporaryFile(delete=True)
            image_temp.write(response.content)
            image_temp.flush()

            # Random payed/free
            requirement = random.choice(["payed", "free"])
            price = random.randint(10000, 100000) if requirement == "payed" else None

            event = Event(
                name=fake.sentence(nb_words=3),
                edu_center=edu_center,
                branch=branch,
                date=fake.date_between(start_date="-10d", end_date="+30d"),
                start_time=fake.time_object(),  # 'time' emas, 'start_time'
                description=fake.text(max_nb_chars=300),
                link=fake.url(),
                is_archived=False,
                requirements=requirement,
                price=price,
            )

            event.picture.save(f"{fake.slug()}.jpg", File(image_temp), save=True)

        self.stdout.write(
            self.style.SUCCESS("✅ 50 ta Event muvaffaqiyatli yaratildi.")
        )
