# Generated by Django 5.2.1 on 2025-06-01 10:09

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0006_remove_branch_city_remove_branch_country_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="branch",
            name="phone_number",
            field=models.CharField(
                blank=True,
                max_length=15,
                null=True,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Telefon raqam quyidagi formatda bo‘lishi kerak: +998901234567",
                        regex="^\\+?998\\d{9}$",
                    )
                ],
            ),
        ),
        migrations.AddField(
            model_name="branch",
            name="work_time",
            field=models.CharField(
                blank=True,
                help_text="Ish vaqti, masalan: 09:00-18:00",
                max_length=50,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="branch",
            name="longitude",
            field=models.DecimalField(
                blank=True, decimal_places=7, max_digits=11, null=True
            ),
        ),
    ]
