# Generated by Django 4.1.7 on 2023-02-25 22:50

import django.contrib.postgres.fields
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('image_uploader', '0009_alter_accounttier_thumbnail_heights'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accounttier',
            name='thumbnail_heights',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(10), django.core.validators.MaxValueValidator(1000)]), default=list, size=None),
        ),
    ]
