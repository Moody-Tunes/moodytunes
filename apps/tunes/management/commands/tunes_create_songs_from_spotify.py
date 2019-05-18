import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management import CommandError

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

        :param tracks: (list) List of dictionaries containing data to store for Song objects
        :return: (tuple(int, int)) Number of tracks successfully processed and failed to process
        """
        success, fail = 0, 0
        for track in tracks:
            # Decode track data name/artist from unicode to string
            track['name'] = track['name'].decode('utf-8')
            track['artist'] = track['artist'].decode('utf-8')

            # Check if song with name and artist already exists in our system
            # For some reason, Spotify codes are not unique across songs and there is a potential
            # for the same to be present multiple times with different song codes
            existing_songs = Song.objects.filter(name=track['name'], artist=track['artist'])
            if existing_songs.exists():
                self.write_to_log_and_output('Song {} by {} already exists in our database'.format(
                    track['name'],
                    track['artist']
                ))
                fail += 1
                continue

            try:
                song, created = Song.objects.get_or_create(code=track['code'], defaults=track)

                if created:
                    msg = 'Created song with code {}'.format(song.code)
                    self.write_to_log_and_output(msg)
                    success += 1
                else:
                    msg = 'Song with code {} already exists'.format(song.code)
                    self.write_to_log_and_output(msg)
                    fail += 1
            except ValidationError:
                msg = 'ERROR: Could not create song with data: {}'.format(track)
                self.write_to_log_and_output(msg, output_stream='stderr', log_level=logging.WARNING)
                fail += 1

        return success, fail

    def get_tracks_from_spotify(self):
        """
        Request, format, and return tracks from Spotify's API.

        :return: (list(dict)) Track data for saving as Song records
        """
        spotify = SpotifyClient(identifier=self._unique_id)
        tracks = []

        for category in settings.SPOTIFY['categories']:
            songs_from_category = 0

            try:
                playlists = spotify.get_playlists_for_category(category, settings.SPOTIFY['max_playlist_from_category'])
                self.logger.info('{} - Got {} playlists for category: {}'.format(
                    self._unique_id,
                    len(playlists),
                    category
                ))

                for playlist in playlists:
                    if songs_from_category < settings.SPOTIFY['max_songs_from_category']:
                        num_tracks = settings.SPOTIFY['max_songs_from_category'] - songs_from_category
                        self.logger.info('{} - Calling Spotify API to get {} track(s) for playlist {}'.format(
                            self._unique_id,
                            num_tracks,
                            playlist['uri']
                        ))
                        raw_tracks = spotify.get_songs_from_playlist(playlist, num_tracks)

                        self.logger.info('{} - Calling Spotify API to get feature data for {} tracks'.format(
                            self._unique_id,
                            len(raw_tracks)
                        ))
                        complete_tracks = spotify.get_audio_features_for_tracks(raw_tracks)

                        # Add genre information to each track. We can use the category search term as the genre
                        # for songs found for that category
                        for track in complete_tracks:
                            track.update({'genre': category})

                        self.logger.info('{} - Got {} tracks from {}'.format(
                            self._unique_id,
                            len(complete_tracks),
                            playlist['name']
                        ))

                        tracks.extend(complete_tracks)
                        songs_from_category += len(complete_tracks)

                self.write_to_log_and_output('Finished processing {} tracks for category: {}'.format(
                    songs_from_category,
                    category
                ))

            except SpotifyException as exc:
                self.write_to_log_and_output(
                    'Error connecting to Spotify! Exception detail: {}. '
                    'Got {} track(s) successfully.'.format(exc, len(tracks)),
                    output_stream='stderr',
                    log_level=logging.WARNING
                )

                break

            except Exception as exc:
                self.write_to_log_and_output(
                    'Unhandled exception when collecting songs from Spotify! Exception detail: {}. '
                    'Got {} track(s) successfully.'.format(exc, len(tracks)),
                    output_stream='stderr',
                    log_level=logging.ERROR
                )

                break

        return tracks

    def handle(self, *args, **options):
        self.write_to_log_and_output('Starting run to create songs from Spotify')

        tracks = self.get_tracks_from_spotify()

        if not tracks:
            # If we didn't get any tracks back from Spotify, raise an exception
            # This will get caught by the periodic task and retry the script again
            self.write_to_log_and_output(
                'Failed to fetch any tracks from Spotify',
                output_stream='stderr',
                log_level=logging.WARNING
            )

            raise CommandError('Failed to fetch any songs from Spotify')

        self.write_to_log_and_output('Got {} tracks from Spotify'.format(len(tracks)))

        succeeded, failed = self.save_songs_to_database(tracks)

        self.write_to_log_and_output('Saved {} songs to database'.format(succeeded))
        self.write_to_log_and_output('Failed to process {} songs'.format(failed))

        self.stdout.write('Done!')
