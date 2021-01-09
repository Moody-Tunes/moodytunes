from django.conf import settings
from django.db.models.signals import post_save
from django.db.transaction import on_commit
from spotify.models import SpotifyAuth
from spotify.tasks import UpdateTopArtistsFromSpotifyTask


def update_spotify_top_artists(sender, instance, created, *args, **kwargs):
    if created:
        on_commit(lambda: UpdateTopArtistsFromSpotifyTask().delay(instance.pk))


post_save.connect(
    update_spotify_top_artists,
    sender=SpotifyAuth,
    dispatch_uid=settings.ADD_SPOTIFY_DATA_TOP_ARTISTS_SIGNAL_UID
)
