from django.conf import settings
from django.core.cache import cache

from tunes.models import Song


def generate_browse_playlist(
        energy,
        valence,
        danceability,
        strategy=None,
        limit=None,
        jitter=None,
        artist=None,
        top_artists=None,
        songs=None
):
    """
    Build a browse playlist of songs for the given criteria.

    Given the attributes to search for, will return a list of songs based on the criteria.

    To have more control over the variability of songs returned, specify a `strategy`
    to use in looking up songs. This will force the query to only  use the `strategy`
    attribute specified when filtering songs.
        Example: specifying `energy` as the strategy will only filter
        songs by the given energy, plus and minus the jitter.

    :param energy: (float) Energy estimate of `Song` records returned
    :param valence: (float) Valence estimate of `Song` records returned
    :param danceability: (float) Danceability estimate of `Song` records returned
    :param strategy: (str) Attribute to use in filtering playlist
    :param limit: (int) Optional max numbers of songs to return (can return fewer than the limit!)
    :param artist: (str) Optional artist of songs to return
    :param jitter: (float) Optional "shuffle" for the boundary box to give users songs from outside their norm
    :param top_artists: (list[str]) Optional array of top artists for user in Spotify to use in search
    :param songs: (QuerySet) Optional queryset of songs to filter

    :return playlist: (QuerySet) `QuerySet` of `Song` instances for the given parameters
    """
    energy_lower_limit = energy_upper_limit = energy
    valence_lower_limit = valence_upper_limit = valence
    danceability_lower_limit = danceability_upper_limit = danceability

    if songs is None:
        songs = Song.objects.all()

    if jitter:
        energy_lower_limit -= jitter
        energy_upper_limit += jitter

        valence_lower_limit -= jitter
        valence_upper_limit += jitter

        danceability_lower_limit -= jitter
        danceability_upper_limit += jitter

    params = {
        'energy__gte': energy_lower_limit,
        'energy__lte': energy_upper_limit,
        'valence__gte': valence_lower_limit,
        'valence__lte': valence_upper_limit,
        'danceability__gte': danceability_lower_limit,
        'danceability__lte': danceability_upper_limit
    }

    # Use a singular attribute for generating browse playlist if specified
    # Instead of using all attributes for filtering songs, only use one of
    # the datapoints we have for song emotion affect
    if strategy:
        if strategy not in settings.BROWSE_PLAYLIST_STRATEGIES:
            raise ValueError(
                'Invalid strategy, must be one of: {}'.format(', '.join(settings.BROWSE_PLAYLIST_STRATEGIES))
            )

        params = {key: params[key] for key in params if key.startswith(strategy)}

    playlist = songs.filter(**params)

    # Filter by artist if provided
    if artist:
        playlist = playlist.filter(artist__icontains=artist)

    playlist = playlist.order_by('?')

    # Filter by user top artists on Spotify if provided
    if top_artists:
        top_artists_playlist = playlist.filter(artist__in=top_artists)

        if top_artists_playlist:

            if limit and top_artists_playlist.count() < limit:
                # If playlist filtered by top artists contains fewer songs than the limit,
                # fill it out with songs from other artists. This ensures we don't return
                # a small playlist if the top artist playlist is less than the desired limit
                filler_track_count = limit - top_artists_playlist.count()
                top_artists_playlist = top_artists_playlist.union(
                    playlist.exclude(id__in=top_artists_playlist)[:filler_track_count]
                )

            playlist = top_artists_playlist

    if limit:
        playlist = playlist[:limit]

    return playlist


class CachedPlaylistManager(object):
    """Facilitates caching and retrieving the last previous user browse playlists"""

    def _make_cache_key(self, user):
        """
        Make a cache key for storing the last previously seen playlist for the user

        :param user: (MoodyUser) User in our system to create a cache key

        :return: (str) Cache key to use in storing/retrieving last seen playlist for user
        """
        return 'browse:{}'.format(user.username)

    def cache_browse_playlist(self, user, playlist, emotion, context, description):
        """
        Cache the playlist generated by the user for use in retrieving the last seen playlist

        :param user: (MoodyUser) User object to associate with cached playlist
        :param playlist: (QuerySet) Playlist recently generated by the user
        :param emotion: (str) Emotion user requested for the browse playlist
        :param context: (str) Optional context set when generating the browse playlist
        :param description: (str) Optional description set when generating the browse playlist
        """
        cache_key = self._make_cache_key(user)
        cache_data = {
            'emotion': emotion,
            'context': context,
            'description': description,
            'playlist': playlist
        }
        cache.set(cache_key, cache_data, settings.BROWSE_PLAYLIST_CACHE_TIMEOUT)

    def retrieve_cached_browse_playlist(self, user):
        """
        Retrieve the cached playlist for user if one exists, else return None

        :param user: (MoodyUser) User in our system to use in cache functionality

        :return: Cached browse playlist or None
        """
        cache_key = self._make_cache_key(user)
        return cache.get(cache_key)
