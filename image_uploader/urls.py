from django.urls import path
from .views import ImageUploadView
from django.conf import settings
from django.conf.urls.static import static
from .views import ObtainAuthTokenView, UserImageListView, ImageOriginalView, ImageThumbnailView, GetExpiringLinkView, ExpiringLinkView

urlpatterns = [
    path('api/token/', ObtainAuthTokenView.as_view(), name='token_obtain_pair'),
    path('upload/', ImageUploadView.as_view(), name='image_upload'),
    path('images/thumbnails/<path:path>/<int:height>',
         ImageThumbnailView.as_view(), name='get_thumbnail'),
    path('images/<path:path>',
         ImageOriginalView.as_view(), name='get_image'),
    path('expiring-link/<path:path>/<int:height>/<int:expire>',
         GetExpiringLinkView.as_view(), name='get_expiring_url'),
    path('expiring-link/<path:path>/<int:expire>',
         GetExpiringLinkView.as_view(), name='get_expiring_url'),
    path('expiring-data/images/',
         ExpiringLinkView.as_view(), name='use_expiring_url'),
    path('list_images/',
         UserImageListView.as_view(), name='user_image_list'),
]
