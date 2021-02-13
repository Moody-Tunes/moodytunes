import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management import CommandError
from spotify_client import SpotifyClient
from spotify_client.exceptions import SpotifyException

from base.management.commands import MoodyBaseCommand
from libs.moody_logging import auto_fingerprint, update_logging_data
from tunes.models import Song


class Command(MoodyBaseCommand):
    help = 'Management command to fetch and create songs from Spotify API'

    def save_songs_to_database(self, tracks):
        """
        Given a list of parameters for Song records, create the objects in the database.

        :param tracks: (list[dict]) List of dictionaries containing data to store for Song records

        :return: (tuple(int, int)) Number of songs successfully saved and number of songs failed to save
        """
        success, fail = 0, 0
        for track in tracks:
            # Check if song with name and artist already exists in our system
            # There is the potential for a song by an artist to be present in
            # Spotify's system multiple times, each with a different Spotify code.
            if Song.objects.filter(name=track['name'], artist=track['artist']).exists():
                self.stdout.write('Song {} by {} already exists in our database'.format(
                    track['name'],
                    track['artist']
                ))
                fail += 1
                continue

            try:
                song, created = Song.objects.get_or_create(code=track['code'], defaults=track)

                if created:
                    self.stdout.write('Created song with code {}'.format(song.code))
                    success += 1
                else:
                    self.stdout.write('Song with code {} already exists'.format(song.code))
                    fail += 1
            except ValidationError:
                self.stderr.write('ERROR: Could not create song with data: {}'.format(track))
                fail += 1

        return success, fail

    @update_logging_data
    def get_tracks_from_spotify(self, **kwargs):
        """
        Request, format, and return tracks from Spotify's API.

        :return: (list(dict)) Track data for saving as Song records
        """
        spotify = SpotifyClient(identifier='create_songs_from_spotify-{}'.format(self._unique_id))

        tracks = []

        for category in settings.SPOTIFY['categories']:
            songs_from_category = 0

            try:
                playlists = spotify.get_playlists_for_category(category, settings.SPOTIFY['max_playlist_from_category'])
                self.logger.info(
                    'Got {} playlists for category: {}'.format(len(playlists), category),
                    extra={
                        'fingerprint': auto_fingerprint('retrieved_playlists_for_category', **kwargs),
                        'command_id': self._unique_id
                    }
                )

                for playlist in playlists:
                    if songs_from_category < settings.SPOTIFY['max_songs_from_category']:
                        num_tracks = settings.SPOTIFY['max_songs_from_category'] - songs_from_category
                        self.logger.info(
                            'Calling Spotify API to get {} track(s) for playlist {}'.format(
                                num_tracks,
                                playlist['name']
                            ),
                            extra={
                                'fingerprint': auto_fingerprint('get_tracks_from_playlist', **kwargs),
                                'tracks_to_retrieve': num_tracks,
                                'command_id': self._unique_id
                            }
                        )

                        raw_tracks = spotify.get_songs_from_playlist(playlist, num_tracks)

                        self.logger.info(
                            'Calling Spotify API to get feature data for {} tracks'.format(len(raw_tracks)),
                            extra={
                                'fingerprint': auto_fingerprint('get_feature_data_for_tracks', **kwargs),
                                'command_id': self._unique_id
                            }
                        )

                        complete_tracks = spotify.get_audio_features_for_tracks(raw_tracks)

                        # Add genre information to each track. We can use the category search term as the genre
                        # for songs found for that category
                        for track in complete_tracks:
                            track.update({'genre': category})

                        self.logger.info(
                            'Got {} tracks from {}'.format(len(complete_tracks), playlist['name']),
                            extra={
                                'fingerprint': auto_fingerprint('retrieved_tracks_from_playlist', **kwargs),
                                'command_id': self._unique_id
                            }
                        )

                        tracks.extend(complete_tracks)
                        songs_from_category += len(complete_tracks)

                self.write_to_log_and_output(
                    'Finished processing {} tracks for category: {}'.format(songs_from_category, category),
                    extra={'fingerprint': auto_fingerprint('processed_tracks_for_category', **kwargs)}
                )

            except SpotifyException as exc:
                self.write_to_log_and_output(
                    'Error connecting to Spotify! Exception detail: {}. '
                    'Got {} track(s) successfully.'.format(exc, len(tracks)),
                    output_stream='stderr',
                    log_level=logging.ERROR,
                    extra={'fingerprint': auto_fingerprint('caught_spotify_exception', **kwargs)},
                    exc_info=True,
                )

                break

            except Exception as exc:
                self.write_to_log_and_output(
                    'Unhandled exception when collecting songs from Spotify! Exception detail: {}. '
                    'Got {} track(s) successfully.'.format(exc, len(tracks)),
                    output_stream='stderr',
                    log_level=logging.ERROR,
                    extra={'fingerprint': auto_fingerprint('caught_unhandled_exception', **kwargs)},
                    exc_info=True,
                )

                break

        return tracks

    @update_logging_data
    def handle(self, *args, **options):
        self.write_to_log_and_output(
            'Starting run to create songs from Spotify',
            extra={'fingerprint': auto_fingerprint('start_create_songs_from_spotify', **options)}
        )

        tracks = self.get_tracks_from_spotify()

        if not tracks:
            # If we didn't get any tracks back from Spotify, raise an exception
            # This will get caught by the periodic task and retry the script again
            self.write_to_log_and_output(
                'Failed to fetch any tracks from Spotify',
                output_stream='stderr',
                log_level=logging.WARNING,
                extra={'fingerprint': auto_fingerprint('failed_to_fetch_tracks_from_spotify', **options)}
            )

            raise CommandError('Failed to fetch any songs from Spotify')

        self.write_to_log_and_output(
            'Got {} tracks from Spotify'.format(len(tracks)),
            extra={
                'fingerprint': auto_fingerprint('fetched_tracks_from_spotify', **options),
                'fetched_tracks': len(tracks)
            }
        )

        succeeded, failed = self.save_songs_to_database(tracks)

        self.write_to_log_and_output(
            'Finished run to create songs from Spotify',
            extra={
                'fingerprint': auto_fingerprint('finish_create_songs_from_spotify', **options),
                'saved_tracks': succeeded,
                'failed_tracks': failed
            }
        )

        return 'Created Songs: {}'.format(succeeded)
