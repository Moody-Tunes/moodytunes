from rest_framework.pagination import PageNumberPagination


class PlaylistPaginator(PageNumberPagination):
    page_size = 10
