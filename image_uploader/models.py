from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
import PIL.Image
import os

User = settings.AUTH_USER_MODEL


class UploadedImage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/')

    def __str__(self) -> str:
        return self.image.name

    def get_image_file(self) -> PIL.Image:
        img = PIL.Image.open(self.image.path)
        return img

    @property
    def image_url(self) -> str:
        return self.image.url

    @property
    def image_name(self) -> str:
        return os.path.basename(self.image.name)


class AccountTier(models.Model):
    name = models.CharField(max_length=64, unique=True, )
    thumbnail_heights = ArrayField(
        models.PositiveIntegerField(
            validators=[
                MinValueValidator(10),
                MaxValueValidator(1000),
            ],
        ), default=list, blank=True)
    access_to_original_image = models.BooleanField(default=False)
    expiring_link_creation = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    tier = models.ForeignKey(AccountTier, on_delete=models.PROTECT, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.username
