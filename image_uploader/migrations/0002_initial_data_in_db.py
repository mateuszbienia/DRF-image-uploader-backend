from django.contrib.auth.models import User
from django.db import migrations
from django.contrib.auth import get_user_model

def create_superuser(apps, schema_editor):
    User = get_user_model()
    User.objects.create_superuser('admin', 'admin@example.com', 'password')

def create_initial_tiers(apps, schema_editor):
    AccountTier = apps.get_model('image_uploader', 'AccountTier')
    AccountTier.objects.create(
        name="Basic", 
        thumbnail_heights=[200])
    AccountTier.objects.create(
        name="Premium", 
        thumbnail_heights=[200, 400],
        access_to_original_image=True)
    AccountTier.objects.create(
        name="Enterprise", 
        thumbnail_heights=[200, 400],
        access_to_original_image=True,
        expiring_link_creation=True)

class Migration(migrations.Migration):

    dependencies = [
        ('image_uploader', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_superuser),
        migrations.RunPython(create_initial_tiers),
    ]