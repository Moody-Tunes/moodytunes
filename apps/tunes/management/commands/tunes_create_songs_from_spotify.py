import logging

from django.conf import settings

from base.management.commands import MoodyBaseCommand
from libs.moody_logging import format_module_name_with_project_prefix
from libs.spotify import SpotifyClient

module_name = format_module_name_with_project_prefix(__name__)
logger = logging.getLogger(module_name)


class Command(MoodyBaseCommand):
    """Management command to fetch and create songs from Spotify API"""

    def handle(self, *args, **options):
        logger.info('{} - Starting run to create songs from Spotify'.format(self._unique_id))

        # TODO: Read these values from options
        num_playlists = 10
        total_songs = 0
        max_tracks_from_playlist = settings.SPOTIFY['max_songs_from_list']
        max_tracks_from_category = settings.SPOTIFY['max_songs_from_category']

        spotify = SpotifyClient(command_id=self._unique_id)

        tracks = []

        for category in settings.SPOTIFY['categories']:
            songs_from_category = 0

            playlists = spotify.get_playlists_for_category(category, num_playlists)

            for playlist in playlists:
                raw_tracks = spotify.get_songs_from_playlist(playlist, max_tracks_from_playlist)
                new_tracks = spotify.get_audio_features_for_tracks(raw_tracks)

                tracks.extend(new_tracks)
                songs_from_category += len(new_tracks)
                total_songs += len(new_tracks)

                if songs_from_category >= max_tracks_from_category:
                    break

        logger.info('Got {} tracks from categories'.format(total_songs))
