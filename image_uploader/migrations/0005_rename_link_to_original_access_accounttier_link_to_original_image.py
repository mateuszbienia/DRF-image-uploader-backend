# Generated by Django 4.1.7 on 2023-02-23 19:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('image_uploader', '0004_alter_accounttier_thumbnail_heights'),
    ]

    operations = [
        migrations.RenameField(
            model_name='accounttier',
            old_name='link_to_original_access',
            new_name='link_to_original_image',
        ),
    ]