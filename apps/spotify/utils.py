from accounts.models import UserSongVote
from tunes.utils import filter_duplicate_votes_on_song_from_playlist


class ExportPlaylistHelper(object):
    @staticmethod
    def get_export_playlist_for_user(user, emotion, genre=None, context=None):
        """
        Build a playlist of songs that a user wants to export to Spotify based on the songs
        they have voted on for an emotion. This function returns the song URIs used for
        adding songs to a playlist on Spotify.

        :param user: (MoodyUser) User record in database that is triggering the export
        :param emotion: (str) Database constant of emotion name the user wants to export
        :param genre: (str) Name of genre for songs the user wants to export
        :param context: (str) Name of context for votes the user wants to export

        :return: (list) List of Spotify song URIs for the playlist to build in Spotify
        """
        votes = UserSongVote.objects.filter(user=user, emotion__name=emotion, vote=True)

        if genre:
            votes = votes.filter(song__genre=genre)

        if context:
            votes = votes.filter(context=context)

        return list(filter_duplicate_votes_on_song_from_playlist(votes).values_list('song__code', flat=True))
