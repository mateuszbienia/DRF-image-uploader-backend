# Generated by Django 4.1.7 on 2023-02-23 19:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('image_uploader', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='tier',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='image_uploader.accounttier'),
        ),
    ]
