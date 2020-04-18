from base.management.commands import MoodyBaseCommand

from tunes.models import Song
from tunes.tasks import update_song_danceabilty


class Command(MoodyBaseCommand):

    def handle(self, *args, **options):
        songs_without_danceability = Song.objects.filter(danceability=0)

        self.write_to_log_and_output('Backfilling {} songs without danceability'.format(
                songs_without_danceability.count()
            )
        )

        for song in songs_without_danceability:
            self.write_to_log_and_output('Calling task to update song {} danceability'.format(song.code))
            update_song_danceabilty.delay(song.pk)
