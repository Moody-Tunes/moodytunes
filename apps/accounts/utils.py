def filter_duplicate_votes_on_song_from_playlist(user_votes):
    """
    Filter queryset of UserSongVotes on unique songs (prevent the same song from appearing twice in the playlist
    even if there are multiple votes for the song)

    :param user_votes: (QuerySet) Collection of votes a user has previously voted as making them feel an Emotion

    :return: (Queryset) Collection of votes without duplicate votes for the same song
    """
    return user_votes.distinct('song__code')
