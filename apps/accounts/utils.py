from accounts.models import UserSongVote


def filter_duplicate_votes_on_song_from_playlist(user_votes):
    """
    Filter queryset of UserSongVotes on unique songs (prevent the same song from appearing twice in the playlist
    even if there are multiple votes for the song)

    :param user_votes: (QuerySet) Collection of votes a user has previously voted as making them feel an Emotion

    :return: (Queryset) Collection of votes without duplicate votes for the same song
    """
    vote_ids = user_votes.distinct('song__code').values_list('id', flat=True)

    return UserSongVote.objects.select_related('emotion', 'song').filter(id__in=vote_ids).order_by('-created')
