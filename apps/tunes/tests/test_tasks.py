from unittest import mock

from django.test import TestCase

from tunes.models import Song
from tunes.tasks import create_songs_from_spotify_task, update_song_danceabilty
from libs.spotify import SpotifyException
from libs.tests.test_utils import MoodyUtil


class TestCreateSongsFromSpotifyTask(TestCase):
    @mock.patch('tunes.tasks.open')
    @mock.patch('tunes.tasks.call_command')
    def test_task_calls_create_songs_command(self, mock_call_command, mock_open):
        mock_output = mock.Mock()
        mock_open.return_value.__enter__.return_value = mock_output

        create_songs_from_spotify_task.run()

        mock_call_command.assert_called_once_with(
            'tunes_create_songs_from_spotify',
            stdout=mock_output,
            stderr=mock_output
        )

    @mock.patch('tunes.tasks.open')
    @mock.patch('libs.spotify.SpotifyClient._make_spotify_request')
    @mock.patch('tunes.tasks.create_songs_from_spotify_task.retry')
    def test_task_retries_if_exception_is_raised(self, mock_retry, mock_spotify_request, mock_open):
        mock_output = mock.Mock()
        mock_open.return_value.__enter__.return_value = mock_output
        mock_spotify_request.side_effect = Exception

        create_songs_from_spotify_task.run()

        mock_retry.assert_called_once()


class TestUpdateSongDanceabilityTask(TestCase):

    @mock.patch('libs.spotify.SpotifyClient.get_audio_features_for_tracks')
    def test_happy_path(self, mock_track_features):
        song = MoodyUtil.create_song()
        mock_track_features.return_value = [{'danceability': .5}]

        update_song_danceabilty.run(song.pk)
        song.refresh_from_db()

        self.assertEqual(song.danceability, .5)

    def test_song_not_found_raises_error(self):
        with self.assertRaises(Song.DoesNotExist):
            update_song_danceabilty.run(99999)  # Non-existent song code

    @mock.patch('libs.spotify.SpotifyClient.get_audio_features_for_tracks')
    @mock.patch('tunes.tasks.update_song_danceabilty.retry')
    def test_task_retries_if_spotify_exception_is_raised(self, mock_retry, mock_track_features):
        song = MoodyUtil.create_song()
        mock_track_features.side_effect = SpotifyException

        update_song_danceabilty.run(song.pk)

        mock_retry.assert_called_once()

    @mock.patch('libs.spotify.SpotifyClient.get_audio_features_for_tracks')
    @mock.patch('tunes.tasks.update_song_danceabilty.retry')
    def test_base_exception_raises_error(self, mock_retry, mock_track_features):
        song = MoodyUtil.create_song()
        mock_track_features.side_effect = Exception

        with self.assertRaises(Exception):
            update_song_danceabilty.run(song.pk)
