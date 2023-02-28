from urllib.request import Request
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UploadedImageSerializer
from rest_framework import status, permissions
from django.http import HttpResponse
from django.conf import settings
from image_uploader.models import UploadedImage
import os
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404
from image_uploader.models import UploadedImage
from io import BytesIO
from .utils import resize_image_by_height, create_image_url_dict
from typing import List
from django.urls import reverse
import datetime
from django.utils import timezone
from requests.exceptions import RequestException
import requests
from django.core.signing import SignatureExpired, BadSignature, Signer


class ObtainAuthTokenView(ObtainAuthToken):
    renderer_classes = settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]


class ImageUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)

    def post(self, request: Request, *args, **kwargs):
        serializer = UploadedImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            user_tier = request.user.tier
            response = {}
            response[serializer.data["image"]] = create_image_url_dict(
                request, serializer.data["image"], user_tier.access_to_original_image, user_tier.thumbnail_heights)
            return Response(response, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ImageOriginalView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request: Request, path: str) -> Response:
        user_tier = request.user.tier
        user_id = request.user.id

        if not user_tier.access_to_original_image:
            return Response({"error": "The requested original image is not allowed for this user's tier"}, status=status.HTTP_400_BAD_REQUEST)
        file_name = os.path.basename(path)
        image = get_object_or_404(
            UploadedImage, user=user_id, image="images/" + file_name)
        try:
            image_pil = image.get_image_file()
            output = BytesIO()
            image_pil.save(output, format=image_pil.format)
            response = HttpResponse(
                output.getvalue(), content_type='image/'+image_pil.format)
            return response
        except IOError:
            return Response({"error": "Unable to read image file"}, status=status.HTTP_400_BAD_REQUEST)


class ImageThumbnailView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, path: str, height: int) -> Response:
        user_tier = request.user.tier
        user_id = request.user.id
        if height is not None:
            if not self.is_valid_thumbnail_height(user_tier.thumbnail_heights, height):
                return Response({"error": "The requested thumbnail height is not allowed for this user's tier"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "No thumbnail size provided"}, status=status.HTTP_400_BAD_REQUEST)

        file_name = os.path.basename(path)
        image = get_object_or_404(
            UploadedImage, user=user_id, image="images/" + file_name)
        try:
            image_pil = image.get_image_file()
            if height is not None:
                image_pil = resize_image_by_height(image_pil, height)
            output = BytesIO()
            image_pil.save(output, format=image_pil.format)
            response = HttpResponse(
                output.getvalue(), content_type='image/'+image_pil.format)
            return response
        except IOError:
            return Response({"error": "Unable to read image file"}, status=status.HTTP_400_BAD_REQUEST)

    def is_valid_thumbnail_height(self, thumbnail_heights: List[int], thumbnail_height) -> bool:
        return thumbnail_height in thumbnail_heights


class GetExpiringLinkView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        path = kwargs.get('path', '')
        height = kwargs.get('height', None)
        expire = kwargs.get('expire', None)

        if not request.user.tier.expiring_link_creation:
            return Response({"error": "The requested operation is not allowed for this user's tier"}, status=status.HTTP_400_BAD_REQUEST)

        if not path:
            return Response({"error": "No image name provided"}, status=status.HTTP_400_BAD_REQUEST)

        if not height:
            is_thumbnail = False
            image_url = request.build_absolute_uri(
                reverse('get_image', args=[path]))
        else:
            is_thumbnail = True
            image_url = request.build_absolute_uri(
                reverse('get_thumbnail', args=[path, height]))

        try:
            expire_seconds = int(expire)
            if expire_seconds < 300 or expire_seconds > 30000:
                raise ValueError(
                    'Expiration time must be between 300 and 30000 seconds')
        except ValueError:
            return Response({"error": "Expiration time must be an integer between 300 and 30000"}, status=status.HTTP_400_BAD_REQUEST)

        expire_at = timezone.now() + timezone.timedelta(seconds=expire_seconds)
        expire_at = expire_at.isoformat()
        expiring_url = request.build_absolute_uri(
            self.generate_expiring_url(image_url, expire_at))

        response_data = {
            'expiring_url': expiring_url,
            'image_url': image_url,
            'is_thumbnail': is_thumbnail,
            'height': height,
            'expire_at': expire_at,
        }

        return Response(response_data)

    def generate_expiring_url(self, url: str, expire_at) -> str:
        signer = Signer()
        signature = signer.sign_object({"url": url, "expires_at": expire_at})
        url = reverse('use_expiring_url') + '?signature=' + signature
        return url


class ExpiringLinkView(APIView):
    def get(self, request):
        signature = request.GET.get('signature', '')
        signer = Signer()
        try:
            signed_data = signer.unsign_object(signature)
            url = signed_data['url']
            expires_at = datetime.datetime.fromisoformat(
                signed_data['expires_at'])
            if expires_at < timezone.now():
                return Response({"error": "URL has expired"}, status=status.HTTP_400_BAD_REQUEST)
        except SignatureExpired:
            return Response({"error": "URL has expired"}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, BadSignature):
            return Response({"error": "Invalid URL"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = request.auth
            headers = {'Authorization': f'Token {token}'}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                content = response.content
                content_type = response.headers['content-type']
                return HttpResponse(content, content_type=content_type)
            else:
                return HttpResponse(status=response.status_code)
        except RequestException as e:
            return Response({"error": "Invalid URL"}, status=status.HTTP_400_BAD_REQUEST)


class UserImageListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request):
        images = UploadedImage.objects.filter(user=request.user.id)
        user_tier = request.user.tier
        image_urls = {}
        for image in images:
            image_urls[image.image_name] = create_image_url_dict(
                request, image.image_name, user_tier.access_to_original_image, user_tier.thumbnail_heights)
        return Response(image_urls)
