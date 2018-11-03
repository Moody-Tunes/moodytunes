import random

from tunes.models import Song


def generate_browse_playlist(lower_bound, upper_bound, exclude_ids=None, limit=None, jitter=None):
    """
    Return a `QuerySet` of `Song` records whose attributes match the desired boundaries as governed from a user's
    `UserEmotion` record for a given `Emotion`

    :@ param lower_bound: (float) Lower bound for attributes of `Song` records returned
    :@ param upper_bound: (float) Upper bound for attributes of `Song` records returned
    :@ param exclude_ids: (list[int]) Optional list of `Song` ids to exclude from the playlist
    :@ param limit: (int) Optional max numbers of songs to return (can return fewer than the limit!)
    :@ param jitter: (float) Optional "shuffle" for the boundary box to give users songs from outside their norm
    :> return playlist: (QuerySet) `QuerySet` of `Song` instances for the given parameters
    """
    if not exclude_ids:
        exclude_ids = []

    if jitter:
        # Flip a coin to determine which attribute we should add jitter to and which one
        # we should subtract the jitter from
        if random.randint(1, 2) % 2 == 0:
            upper_bound += jitter
            lower_bound -= jitter
        else:
            lower_bound += jitter
            upper_bound -= jitter

    playlist = Song.objects.filter(
        valence__gte=lower_bound,
        valence__lte=upper_bound,
        energy__gte=lower_bound,
        energy__lte=upper_bound
    ).exclude(
        id__in=exclude_ids
    )

    if limit:
        playlist = playlist[:limit]

    return playlist
