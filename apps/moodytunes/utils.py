from accounts.models import UserSongVote


class ExportPlaylistHelper(object):
    @staticmethod
    def get_export_playlist_for_user(user, emotion, genre, context):
        """
        Build a playlist of songs that a user wants to export to Spotify

        :param user: (MoodyUser) User record in database that is triggering the export
        :param emotion: (str) Database constant of emotion name the user wants to export
        :param genre: (str) Database constant of genre for songs the user wants to export
        :param context: (str) Database constant of context for votes the user wants to export

        :return: (list) List of Spotify song URIs for the playlist to build in Spotify
        """
        songs = UserSongVote.objects.filter(user=user, emotion__name=emotion, vote=True)

        if genre:
            songs = songs.filter(song__genre=genre)

        if context:
            songs = songs.filter(context=context)

        songs = songs.values_list('song__code', flat=True).distinct()
        songs = list(songs)

        return songs
