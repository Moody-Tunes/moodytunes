from unittest import mock

from django.test import TestCase

from tunes.tasks import create_songs_from_spotify_task


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
