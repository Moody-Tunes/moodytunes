from unittest import mock

from django.test import TestCase

from tunes.tasks import CreateSongsFromSpotifyTask


class TestCreateSongsFromSpotifyTask(TestCase):
    @mock.patch('tunes.tasks.open')
    @mock.patch('tunes.tasks.call_command')
    def test_task_calls_create_songs_command(self, mock_call_command, mock_open):
        mock_output = mock.Mock()
        mock_open.return_value.__enter__.return_value = mock_output

        CreateSongsFromSpotifyTask().run()

        mock_call_command.assert_called_once_with(
            'tunes_create_songs_from_spotify',
            stdout=mock_output,
            stderr=mock_output
        )

    @mock.patch('tunes.tasks.open')
    @mock.patch('spotify_client.SpotifyClient._make_spotify_request')
    @mock.patch('tunes.tasks.CreateSongsFromSpotifyTask.retry')
    def test_task_retries_if_exception_is_raised(self, mock_retry, mock_spotify_request, mock_open):
        mock_output = mock.Mock()
        mock_open.return_value.__enter__.return_value = mock_output
        mock_spotify_request.side_effect = Exception

        CreateSongsFromSpotifyTask().run()

        mock_retry.assert_called_once()
