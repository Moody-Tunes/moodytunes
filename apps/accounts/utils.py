from accounts.models import UserSongVote


def filter_duplicate_votes_on_song_from_playlist(user_votes):
    """
    Filter queryset of UserSongVotes on unique songs (prevent the same song from appearing twice in the playlist
    even if there are multiple votes for the song)

    :param user_votes: (QuerySet) Collection of votes a user has previously voted as making them feel an Emotion
    :return: (Queryset) Collection of votes without duplicate votes for the same song
    """
    votes = []
    already_added_songs = []

    for vote in user_votes:
        if vote.song.id not in already_added_songs:
            votes.append(vote.id)
            already_added_songs.append(vote.song.id)

    # We want to return a queryset so we'll return the UserSongVotes that we've filtered
    # Need to order_by created to maintain behavior of PlaylistView
    return UserSongVote.objects.filter(id__in=votes).order_by('created')
