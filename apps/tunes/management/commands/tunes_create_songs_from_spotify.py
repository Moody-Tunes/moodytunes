import logging

from django.conf import settings

from base.management.commands import MoodyBaseCommand
from tunes.models import Song
from libs.spotify import SpotifyClient, SpotifyException


class Command(MoodyBaseCommand):
    help = 'Management command to fetch and create songs from Spotify API'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

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
                self.write_to_log_and_output(msg)
                fail += 1

        return success, fail

    def handle(self, *args, **options):
        self.logger.info('{} - Starting run to create songs from Spotify'.format(self._unique_id))

        num_playlists = 10
        spotify = SpotifyClient(command_id=self._unique_id)
        tracks = []

        for category in settings.SPOTIFY['categories']:
            songs_from_category = 0

            try:
                playlists = spotify.get_playlists_for_category(category, num_playlists)
                self.write_to_log_and_output('Got {} playlists for category: {}'.format(len(playlists), category))

                for playlist in playlists:
                    raw_tracks = spotify.get_songs_from_playlist(playlist, settings.SPOTIFY['max_songs_from_list'])
                    new_tracks = spotify.get_audio_features_for_tracks(raw_tracks)

                    # Add genre information to each track. We can use the category search term as the genre
                    # for songs found for that category
                    for track in new_tracks:
                        track.update({'genre': category})

                    self.write_to_log_and_output('Got {} tracks from {}'.format(len(new_tracks), playlist['name']))

                    tracks.extend(new_tracks)
                    songs_from_category += len(new_tracks)

                    if songs_from_category >= settings.SPOTIFY['max_songs_from_category']:
                        self.write_to_log_and_output('Retrieved max tracks for category: {}'.format(category))
                        break

            except SpotifyException as exc:
                self.write_to_log_and_output(
                    'Error connecting to Spotify! Exception detail: {}. Proceeding to second phase...'.format(exc),
                    output_stream='stderr',
                    log_level='warning'
                )

                break

        self.write_to_log_and_output('Got {} tracks from Spotify'.format(len(tracks)))

        succeeded, failed = self.save_songs_to_database(tracks)

        self.stdout.write('Saved {} songs to database'.format(succeeded))
        self.stdout.write('Failed to process {} songs'.format(failed))

        self.stdout.write('Done!')
