from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class PlaylistPaginator(PageNumberPagination):
    page_size = settings.PLAYLIST_SIZE
