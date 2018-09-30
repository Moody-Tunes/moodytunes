import logging

from django.conf import settings

from base.management.commands import MoodyBaseCommand
from tunes.models import Song
from libs.spotify import SpotifyClient


class Command(MoodyBaseCommand):
    help = 'Management command to fetch and create songs from Spotify API'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def add_arguments(self, parser):
        parser.add_argument(
            '--total_songs',
            dest='total_songs',
            type=int,
            default=10,
            help='''
            Total number of songs to process during run of this script (default 10).
            Note that it is possible to process FEWER than number specified
            if this script runs into any issues processing tracks.
            '''
        )

    def save_songs_to_database(self, tracks):
        """
        Given a list of parameters for Song records, create the objects in the database.
        :tracks: (list) List of dictionaries containing data to store for Song objects
        @return: Two tuple of amount of tracks that successfully processed and how many failed to process
        """
        success, fail = 0, 0
        for track in tracks:

            song, created = Song.objects.get_or_create(code=track['code'], defaults=track)

            if created:
                msg = 'Created song with code {}'.format(song.code)
                self.write_to_log_and_output(msg)
                success += 1
            else:
                msg = 'Song with code {} already exists'.format(song.code)
                self.write_to_log_and_output(msg, output_stream='stderr')
                fail += 1

        return success, fail

    def handle(self, *args, **options):
        self.logger.info('{} - Starting run to create songs from Spotify'.format(self._unique_id))

        total_songs = options.get('total_songs')
        num_playlists = 10
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

                if songs_from_category >= max_tracks_from_category:
                    break

                if len(tracks) >= total_songs:
                    break

        self.write_to_log_and_output('Got {} tracks from Spotify'.format(len(tracks)))

        succeeded, failed = self.save_songs_to_database(tracks)

        self.stdout.write('Saved {} songs to database'.format(succeeded))
        self.stdout.write('Failed to process {} songs'.format(failed))

        self.stdout.write('Done!')
