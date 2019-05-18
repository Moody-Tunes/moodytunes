import logging

from base.management.commands import MoodyBaseCommand
from tunes.models import Song


class Command(MoodyBaseCommand):
    help = 'Clear duplicate songs from the database'

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def get_duplicate_songs_for_song(self, song):
        """Return all songs in the database that are duplicates of the specified song"""
        return Song.objects.filter(
            name=song.name,
            artist=song.artist
        ).exclude(
            code=song.code
        ).order_by(
            'created'
        )

    def reassign_votes_for_dupe_song_to_canonical_song(self, canonical_song, dupe_song):
        """
        Reassign all votes for the duplicate song to the canonical song
        If a user has voted on both the canonical song and duplicate song, only keep the vote for the canonical song
        :param canonical_song: (Song) Song we will persist in our database for a given name and artist
        :param dupe_song: (Song) Song marked as a duplicate of the canonical song
        """
        dupe_votes = dupe_song.usersongvote_set.count()

        for vote in dupe_song.usersongvote_set.iterator():
            if vote.user.usersongvote_set.filter(song=canonical_song).exists():
                vote.delete()
            else:
                vote.song = canonical_song
                vote.save()

        self.write_to_log_and_output(
            'Reassigned {} votes for song {} to song {}'.format(dupe_votes, dupe_song.code, canonical_song.code)
        )

    def handle(self, *args, **options):
        self.write_to_log_and_output('Starting process to clear duplicate songs from database')
        songs = Song.objects.prefetch_related('usersongvote_set').all()

        for song in songs.iterator():

            if not Song.objects.filter(code=song.code).exists():
                self.write_to_log_and_output('Skipping song {} as it already has been deleted'.format(song.code))
                continue

            duplicate_songs = self.get_duplicate_songs_for_song(song)

            if duplicate_songs.exists():

                dupe_count = duplicate_songs.count()
                self.write_to_log_and_output('Found {} duplicate songs for song {}'.format(dupe_count, song.code))

                # Reassign votes for duplicate songs to the canonical song
                for dupe_song in duplicate_songs:
                    self.reassign_votes_for_dupe_song_to_canonical_song(song, dupe_song)

                duplicate_songs.delete()
                self.write_to_log_and_output('Deleted {} duplicate songs of song {}'.format(dupe_count, song.code))

            else:
                self.write_to_log_and_output('Song {} does not have any duplicate songs. Skipping...'.format(song.code))

        self.write_to_log_and_output('Done process of clearing duplicate songs from database')
