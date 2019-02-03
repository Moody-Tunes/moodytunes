import random

from tunes.models import Song


def generate_browse_playlist(energy, valence, limit=None, jitter=None, songs=None):
    """
    Return a `QuerySet` of `Song` records whose attributes match the desired boundaries as governed from a user's
    `UserEmotion` record for a given `Emotion`

    :param energy: (float) Energy estimate of `Song` records returned
    :param valence: (float) Valence estimate of `Song` records returned
    :param limit: (int) Optional max numbers of songs to return (can return fewer than the limit!)
    :param jitter: (float) Optional "shuffle" for the boundary box to give users songs from outside their norm
    :param songs: (QuerySet) Optional queryset of songs to filter

    :return playlist: (QuerySet) `QuerySet` of `Song` instances for the given parameters
    """
    energy_lower_limit = energy_upper_limit = energy
    valence_lower_limit = valence_upper_limit = valence

    if not songs:
        songs = Song.objects.all()

    if jitter:
        energy_lower_limit -= jitter
        energy_upper_limit += jitter

        valence_lower_limit -= jitter
        valence_upper_limit += jitter

        playlist = songs.filter(
            energy__gte=energy_lower_limit,
            energy__lte=energy_upper_limit,
            valence__gte=valence_lower_limit,
            valence__lte=valence_upper_limit
        )

    else:
        playlist = songs.filter(
            energy=energy,
            valence=valence
        )

    # Shuffle playlist to ensure freshness
    playlist = list(playlist)
    random.shuffle(playlist)

    if limit:
        playlist = playlist[:limit]

    return playlist
