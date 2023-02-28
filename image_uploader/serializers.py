from rest_framework import serializers
from .models import UploadedImage
from django.core.exceptions import ValidationError
from django.conf import settings
import os


class UploadedImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedImage
        fields = ('image', 'image_url')

    def validate_image(self, image):
        self.validate_image_type(image)
        self.validate_image_size(image)
        return image

    def validate_image_type(self, image):
        """
        Validate that the uploaded file is a JPEG or PNG image.
        """
        if not image:
            raise ValidationError("Image file is missing")
        if image.content_type.lower() not in settings.WHITELISTED_IMAGE_TYPES.values():
            raise ValidationError("Only JPEG and PNG images are supported")

    def validate_image_size(self, image):
        if not image:
            raise ValidationError("Image file is missing")
        filesize = image.size
        megabyte_limit = 2.0
        if filesize > megabyte_limit*1024*1024:
            raise ValidationError(f"Maximum file size is {megabyte_limit} MB")

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['image'] = os.path.basename(representation['image_url'])
        return representation
