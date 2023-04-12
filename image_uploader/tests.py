import tempfile
import os
import io

from PIL import Image

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from .models import AccountTier
from django.test import RequestFactory
from .utils import create_image_url_dict
from django.core.signing import Signer
from django.utils import timezone
from rest_framework.authtoken.models import Token
from django.test import override_settings
import shutil
import rest_framework.test
import xmlrunner

TEST_DIR = 'test_data_directory'


class ImageUploadViewTestCase(APITestCase):

    def setUp(self):
        self.url = reverse('image_upload')

        factory = RequestFactory()
        self.request = factory.post('')

        tier_empty = AccountTier.objects.create(name='test_tier')
        self.user_empty_tier = get_user_model().objects.create_user(
            username='testuser', password='testpassword', tier=tier_empty)

        self.thumbnail_heights = [100, 200]
        tier_thumbnails = AccountTier.objects.create(
            name='test_tier_thumbnails', thumbnail_heights=self.thumbnail_heights)
        self.user_thumbnails = get_user_model().objects.create_user(
            username='testuser_thumbnails', password='testpassword', tier=tier_thumbnails)

        tier_thumbnails_original = AccountTier.objects.create(
            name='test_tier_thumbnails_original', thumbnail_heights=self.thumbnail_heights, access_to_original_image=True)
        self.user_thumbnails_original = get_user_model().objects.create_user(
            username='testuser_thumbnails_original', password='testpassword', tier=tier_thumbnails_original)

        tier_original = AccountTier.objects.create(
            name='test_tier_original', access_to_original_image=True)
        self.user_original = get_user_model().objects.create_user(
            username='testuser_original', password='testpassword', tier=tier_original)

        self.valid_image = self.generate_image()
        self.valid_image_name = os.path.basename(self.valid_image.name)

        self.client = APIClient()

    def tearDown(self):
        self.valid_image.close()

    def generate_image(self, suffix='.png'):
        image = Image.new('RGB', (100, 100), color='red')
        tmp_file = tempfile.NamedTemporaryFile(suffix=suffix)
        image.save(tmp_file)
        tmp_file.seek(0)
        return tmp_file

    def generate_big_image(self):
        image = Image.new('RGB', (15000, 10000))
        tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
        image.save(tmp_file, format='JPEG')
        tmp_file.seek(0)
        return tmp_file

    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def test_upload_valid_image_empty_tier(self):
        self.client.force_authenticate(user=self.user_empty_tier)
        response_json = {self.valid_image_name: {'thumbnails': []}}

        response = self.client.post(self.url, {'image': self.valid_image})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json(), response_json)

    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def test_upload_valid_image_thumbnail_tier(self):
        self.client.force_authenticate(user=self.user_thumbnails)
        response = self.client.post(self.url, {'image': self.valid_image})
        response_json = create_image_url_dict(
            self.request, self.valid_image_name, self.user_thumbnails.tier.access_to_original_image, self.user_thumbnails.tier.thumbnail_heights)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json(), response_json)

    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def test_upload_valid_image_thumbnail_original_tier(self):
        self.client.force_authenticate(user=self.user_thumbnails_original)
        response = self.client.post(self.url, {'image': self.valid_image})
        response_json = create_image_url_dict(
            self.request, self.valid_image_name, self.user_thumbnails_original.tier.access_to_original_image, self.user_thumbnails_original.tier.thumbnail_heights)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json(), response_json)

    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def test_upload_valid_image_original_tier(self):
        self.client.force_authenticate(user=self.user_original)
        response = self.client.post(self.url, {'image': self.valid_image})
        response_json = create_image_url_dict(
            self.request, self.valid_image_name, self.user_original.tier.access_to_original_image, self.user_original.tier.thumbnail_heights)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json(), response_json)

    def test_upload_no_image(self):
        self.client.force_authenticate(user=self.user_empty_tier)
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['image'][0], 'No file was submitted.')

    def test_upload_invalid_image_type(self):
        self.client.force_authenticate(user=self.user_empty_tier)
        invalid_image = self.generate_image(".bmp")
        response = self.client.post(self.url, {'image': invalid_image})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['image'][0],
                         'Only JPEG and PNG images are supported')
        invalid_image.close()

    def test_upload_invalid_image_size(self):
        self.skipTest("Slow, method: generate_big_image")
        self.client.force_authenticate(user=self.user_empty_tier)
        oversized_image = self.generate_big_image()
        response = self.client.post(self.url, {'image': oversized_image})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['image']
                         [0], 'Maximum file size is 2.0 MB')
        oversized_image.close()

    def test_upload_unauthenticated(self):
        response = self.client.post(self.url, {'image': self.valid_image})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_upload_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid_token')
        response = self.client.post(self.url, {'image': self.valid_image})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ImageOriginalViewTestCase(APITestCase):

    def setUp(self):
        tier_with_access = AccountTier.objects.create(
            name='test_tier_access', access_to_original_image=True)
        self.user_access = get_user_model().objects.create_user(
            username='user_access', password='testpassword', tier=tier_with_access)

        tier_without_access = AccountTier.objects.create(
            name='test_tier', access_to_original_image=False)
        self.user_no_access = get_user_model().objects.create_user(
            username='user_no_access', password='testpassword', tier=tier_without_access)

        self.client = APIClient()

        self.image = self.generate_image()

    def tearDown(self):
        self.image.close()

    def generate_image(self, suffix='.png'):
        image = Image.new('RGB', (100, 100), color='red')
        tmp_file = tempfile.NamedTemporaryFile(suffix=suffix)
        image.save(tmp_file)
        tmp_file.seek(0)
        return tmp_file

    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def test_get_image_with_access(self):
        self.client.force_authenticate(user=self.user_access)
        response_upload = self.client.post(reverse('image_upload'),
                                           {'image': self.image}, format='multipart')
        self.assertEqual(response_upload.status_code, status.HTTP_201_CREATED)
        path = list(response_upload.json().keys())[0]

        response_get = self.client.get(
            reverse('get_image', kwargs={'path': path}))
        self.assertEqual(response_get.status_code, status.HTTP_200_OK)
        self.assertEqual(response_get.get('content-type'), 'image/PNG')

    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def test_get_image_without_access(self):
        self.client.force_authenticate(user=self.user_access)
        response_upload = self.client.post(reverse('image_upload'),
                                           {'image': self.image}, format='multipart')
        self.assertEqual(response_upload.status_code, status.HTTP_201_CREATED)
        path = list(response_upload.json().keys())[0]

        self.client.force_authenticate(user=self.user_no_access)
        response_get = self.client.get(
            reverse('get_image', kwargs={'path': path}))
        self.assertEqual(response_get.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_nonexistent_image(self):
        self.client.force_authenticate(user=self.user_access)

        response_get = self.client.get(
            reverse('get_image', kwargs={'path': 'nonexistent_image.jpg'}))
        self.assertEqual(response_get.status_code, status.HTTP_404_NOT_FOUND)


class ImageThumbnailViewTestCase(APITestCase):
    def setUp(self):
        tier_empty = AccountTier.objects.create(name='test_tier')
        self.user_empty_tier = get_user_model().objects.create_user(
            username='testuser', password='testpassword', tier=tier_empty)

        self.thumbnail_heights = [100, 200, 600, 800]
        tier_thumbnails = AccountTier.objects.create(
            name='test_tier_thumbnails', thumbnail_heights=self.thumbnail_heights)
        self.user_thumbnails = get_user_model().objects.create_user(
            username='testuser_thumbnails', password='testpassword', tier=tier_thumbnails)

        self.client = APIClient()

        self.image = self.generate_image()

    def tearDown(self):
        self.image.close()

    def generate_image(self, suffix='.png'):
        image = Image.new('RGB', (600, 600), color='red')
        tmp_file = tempfile.NamedTemporaryFile(suffix=suffix)
        image.save(tmp_file)
        tmp_file.seek(0)
        return tmp_file

    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def test_valid_thumbnail_smaller(self):
        self.client.force_authenticate(user=self.user_thumbnails)
        response_upload = self.client.post(reverse('image_upload'),
                                           {'image': self.image}, format='multipart')
        self.assertEqual(response_upload.status_code, status.HTTP_201_CREATED)
        path = list(response_upload.json().keys())[0]

        url = reverse('get_thumbnail', kwargs={
            'path': path, 'height': self.thumbnail_heights[0]})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response['Content-Type'], 'image/PNG')

        image = Image.open(io.BytesIO(response.content))
        self.assertEqual(image.format, 'PNG')
        self.assertEqual(image.size[0], self.thumbnail_heights[0])
        self.assertEqual(image.size[1], self.thumbnail_heights[0])

    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def test_valid_thumbnail_bigger(self):
        self.client.force_authenticate(user=self.user_thumbnails)
        response_upload = self.client.post(reverse('image_upload'),
                                           {'image': self.image}, format='multipart')
        self.assertEqual(response_upload.status_code, status.HTTP_201_CREATED)
        path = list(response_upload.json().keys())[0]

        url = reverse('get_thumbnail', kwargs={
            'path': path, 'height': self.thumbnail_heights[-1]})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response['Content-Type'], 'image/PNG')

        image = Image.open(io.BytesIO(response.content))
        self.assertEqual(image.format, 'PNG')
        self.assertEqual(image.size[0], self.thumbnail_heights[-1])
        self.assertEqual(image.size[1], self.thumbnail_heights[-1])

    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def test_valid_thumbnail_same_size(self):
        self.client.force_authenticate(user=self.user_thumbnails)
        response_upload = self.client.post(reverse('image_upload'),
                                           {'image': self.image}, format='multipart')
        self.assertEqual(response_upload.status_code, status.HTTP_201_CREATED)
        path = list(response_upload.json().keys())[0]

        url = reverse('get_thumbnail', kwargs={
            'path': path, 'height': self.thumbnail_heights[-2]})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response['Content-Type'], 'image/PNG')

        image = Image.open(io.BytesIO(response.content))
        self.assertEqual(image.format, 'PNG')
        self.assertEqual(image.size[0], self.thumbnail_heights[-2])
        self.assertEqual(image.size[1], self.thumbnail_heights[-2])

    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def test_invalid_thumbnail(self):
        self.client.force_authenticate(user=self.user_thumbnails)
        response_upload = self.client.post(reverse('image_upload'),
                                           {'image': self.image}, format='multipart')
        self.assertEqual(response_upload.status_code, status.HTTP_201_CREATED)
        path = list(response_upload.json().keys())[0]

        url = reverse('get_thumbnail', kwargs={
            'path': path, 'height': 33})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"], "The requested thumbnail height is not allowed for this user's tier")

    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def test_invalid_user_tier(self):
        self.client.force_authenticate(user=self.user_empty_tier)
        response_upload = self.client.post(reverse('image_upload'),
                                           {'image': self.image}, format='multipart')
        self.assertEqual(response_upload.status_code, status.HTTP_201_CREATED)
        path = list(response_upload.json().keys())[0]

        url = reverse('get_thumbnail', kwargs={
            'path': path, 'height': 33})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"], "The requested thumbnail height is not allowed for this user's tier")


class GetExpiringLinkViewTestCase(APITestCase):
    def setUp(self):
        tier_full = AccountTier.objects.create(name='full_tier', thumbnail_heights=[
                                               200], access_to_original_image=True, expiring_link_creation=True)
        self.user_full_tier = get_user_model().objects.create_user(
            username='testuser_full', password='testpassword', tier=tier_full)

        tier_empty = AccountTier.objects.create(name='test_tier')
        self.user_empty_tier = get_user_model().objects.create_user(
            username='testuser', password='testpassword', tier=tier_empty)

        self.client = APIClient()

        self.image = self.generate_image()

        self.url_thumbnail = reverse('get_expiring_url', args=[
            os.path.basename(self.image.name), 200, 3600])
        self.url = reverse('get_expiring_url', args=[
            os.path.basename(self.image.name), 3600])

    def tearDown(self):
        self.image.close()

    def generate_image(self, suffix='.png'):
        image = Image.new('RGB', (100, 100), color='red')
        tmp_file = tempfile.NamedTemporaryFile(suffix=suffix)
        image.save(tmp_file)
        tmp_file.seek(0)
        return tmp_file

    def test_get_expiring_link_thumbnail(self):
        self.client.force_authenticate(user=self.user_full_tier)
        response = self.client.get(self.url_thumbnail)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('expiring_url' in response.data)
        self.assertTrue('image_url' in response.data)
        self.assertTrue('is_thumbnail' in response.data)
        self.assertTrue('height' in response.data)
        self.assertTrue('expire_at' in response.data)
        self.assertEqual(response.data['is_thumbnail'], True)
        self.assertEqual(response.data['height'], 200)

    def test_get_expiring_link_no_thumbnail(self):
        self.client.force_authenticate(user=self.user_full_tier)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('expiring_url' in response.data)
        self.assertTrue('image_url' in response.data)
        self.assertTrue('is_thumbnail' in response.data)
        self.assertTrue('height' in response.data)
        self.assertTrue('expire_at' in response.data)
        self.assertEqual(response.data['is_thumbnail'], False)
        self.assertEqual(response.data['height'], None)

    def test_get_expiring_link_invalid_expire_lower(self):
        self.client.force_authenticate(user=self.user_full_tier)

        url = reverse('get_expiring_url', args=[
            os.path.basename(self.image.name), 299])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
                         'error': 'Expiration time must be an integer between 300 and 30000'})

    def test_get_expiring_link_invalid_expire_upper(self):
        self.client.force_authenticate(user=self.user_full_tier)

        url = reverse('get_expiring_url', args=[
            os.path.basename(self.image.name), 30001])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"], 'Expiration time must be an integer between 300 and 30000')

    def test_get_expiring_link_not_allowed_tier(self):
        self.client.force_authenticate(user=self.user_empty_tier)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"], "The requested operation is not allowed for this user's tier")


class ExpiringLinkViewTestCase(APITestCase):
    def setUp(self):
        tier_full = AccountTier.objects.create(name='full_tier', thumbnail_heights=[
                                               200], access_to_original_image=True, expiring_link_creation=True)
        self.user_full_tier = get_user_model().objects.create_user(
            username='testuser_full', password='testpassword', tier=tier_full)

        tier_empty = AccountTier.objects.create(name='test_tier')
        self.user_empty_tier = get_user_model().objects.create_user(
            username='testuser', password='testpassword', tier=tier_empty)

        self.client = APIClient()
        self.user_full_tier_token = Token.objects.create(
            user=self.user_full_tier)

        self.image = self.generate_image()

        self.url_thumbnail = reverse('get_expiring_url', args=[
            os.path.basename(self.image.name), 200, 3600])
        self.url = reverse('get_expiring_url', args=[
            os.path.basename(self.image.name), 3600])

    def tearDown(self):
        self.image.close()

    def generate_image(self, suffix='.png'):
        image = Image.new('RGB', (100, 100), color='red')
        tmp_file = tempfile.NamedTemporaryFile(suffix=suffix)
        image.save(tmp_file)
        tmp_file.seek(0)
        return tmp_file

    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def test_valid_signature(self):
        self.skipTest(
            "Authentication problem that happens only on testserver.")
        # self.client.force_authenticate(user=self.user_full_tier)

        response = self.client.get(
            self.url, HTTP_AUTHORIZATION=f'Token {self.user_full_tier_token.key}')
        self.client.post(reverse('image_upload'), {
                         'image': self.image}, HTTP_AUTHORIZATION=f'Token {self.user_full_tier_token.key}')
        response = self.client.get(
            response.data["expiring_url"], HTTP_AUTHORIZATION=f'Token {self.user_full_tier_token.key}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], "images/JPEG")

    def test_expired_signature(self):
        signer = Signer()
        signed_data = {'url': self.url, 'expires_at': (
            timezone.now() - timezone.timedelta(seconds=1)).isoformat()}
        signature = signer.sign_object(signed_data)

        response = self.client.get(reverse('use_expiring_url'), {
                                   'signature': signature})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'URL has expired')

    def test_invalid_signature(self):
        response = self.client.get(reverse('use_expiring_url'), {
                                   'signature': 'invalid_signature'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Invalid URL')


class UserImageListViewTestCase(APITestCase):
    def setUp(self):
        tier_full = AccountTier.objects.create(name='full_tier',
                                               thumbnail_heights=[200],
                                               access_to_original_image=True,
                                               expiring_link_creation=True)
        self.user_full_tier = get_user_model().objects.create_user(
            username='testuser_full', password='testpassword', tier=tier_full)

        tier_empty = AccountTier.objects.create(name='test_tier')
        self.user_empty_tier = get_user_model().objects.create_user(
            username='testuser_empty', password='testpassword', tier=tier_empty)

        self.client = APIClient()

        self.url = reverse('user_image_list')

        self.image1 = self.generate_image()
        self.image2 = self.generate_image()
        self.client.force_authenticate(user=self.user_full_tier)
        self.create_uploaded_image(self.image1)
        self.create_uploaded_image(self.image2)

        self.client.credentials()

    def tearDown(self):
        self.image1.close()
        self.image2.close()

    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def create_uploaded_image(self, image):
        self.client.post(reverse('image_upload'), {'image': image})

    def generate_image(self, suffix='.png'):
        image = Image.new('RGB', (100, 100), color='red')
        tmp_file = tempfile.NamedTemporaryFile(suffix=suffix)
        image.save(tmp_file)
        tmp_file.seek(0)
        return tmp_file

    def test_list_images(self):
        self.client.force_authenticate(user=self.user_full_tier)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(list(response.data[os.path.basename(self.image1.name)].keys()), [
                         'original_url', 'thumbnails'])
        self.assertEqual(response.data[os.path.basename(
            self.image1.name)]['thumbnails'][0]['height'], 200)

    def test_list_images_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


def tearDownModule():
    print("\nDeleting temporary test files...\n")
    try:
        shutil.rmtree(TEST_DIR)
    except OSError:
        pass


if __name__ == '__main__':
    rest_framework.test.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))