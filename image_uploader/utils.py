from urllib.request import Request
from PIL import Image
from django.urls import reverse


def resize_image_by_height(image: Image, new_height: int) -> Image:
    '''
    This function returns a resized image object with the specified height, keeping the aspect ratio of the original image.
    '''
    file_ext = image.format
    width, height = image.size
    new_width = int(width * new_height / height)
    img = image.resize((new_width, new_height),
                       Image.ANTIALIAS)
    img.format = file_ext
    return img


def create_image_url_dict(request: Request, image_name: str, original_link_access: bool = False, thumbnail_heights: int = []) -> dict:
    '''
    This function returns a dictionary containing image URLs and their corresponding thumbnail URLs with different heights.
    '''
    url_dict = {}
    thumbnail_urls = []
    for height in thumbnail_heights:
        thumbnail_url = {}
        thumbnail_url["height"] = height
        thumbnail_url["url"] = request.build_absolute_uri(reverse('get_thumbnail', kwargs={
            "path": image_name, 'height': height}))
        thumbnail_urls.append(thumbnail_url)
    if original_link_access:
        url_dict["original_url"] = request.build_absolute_uri(
            reverse('get_image', args=[image_name]))
    url_dict["thumbnails"] = thumbnail_urls
    return url_dict
