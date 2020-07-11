# API Keys/Credentials get stored here
from envparse import env


# Spotify OAuth scope constants
SPOTIFY_PLAYLIST_MODIFY_SCOPE = 'playlist-modify-public'
SPOTIFY_TOP_ARTIST_READ_SCOPE = 'user-top-read'

# Spotify Definitions
SPOTIFY = {
    'api_url': env.str('MTDJ_SPOTIFY_API_URL', default='https://api.spotify.com/v1'),
    'auth_url': env.str('MTDJ_SPOTIFY_AUTH_URL', default='https://accounts.spotify.com/api/token'),
    'user_auth_url': env.str('MTDJ_SPOTIFY_USER_AUTH_URL', default='https://accounts.spotify.com/authorize'),
    'client_id': env.str('MTDJ_SPOTIFY_CLIENT_ID', default='__spotify_client_id_not_set__'),
    'secret_key': env.str('MTDJ_SPOTIFY_SECRET_KEY', default='__spotify_secret_key_not_set__'),
    'categories': env.list('MTDJ_SPOTIFY_CATEGORIES', default=['hiphop', 'rock', 'chill']),
    'max_songs_from_list': env.int('MTDJ_SPOTIFY_MAX_SONGS_FROM_LIST', default=10),
    'max_songs_from_category': env.int('MTDJ_SPOTIFY_MAX_SONGS_FROM_CATEGORY', default=25),
    'max_playlist_from_category': env.int('MTDJ_SPOTIFY_MAX_PLAYLISTS_FROM_CATEGORY', default=10),
    'auth_cache_key': env.str('MTDJ_SPOTIFY_AUTH_CACHE_KEY', default='spotify:auth-token'),
    'auth_redirect_uri': env.str('MTDJ_SPOTIFY_REDIRECT_URI', default='https://moodytunes.vm/moodytunes/spotify/callback/'),
    'auth_cache_key_timeout': 60 * 60,  # Authorization token is good for one hour
    'auth_user_token_timeout': 60 * 60,  # User auth token is good for one hour
    'auth_user_scopes': [SPOTIFY_PLAYLIST_MODIFY_SCOPE, SPOTIFY_TOP_ARTIST_READ_SCOPE],
    'max_top_artists': 50,  # Number of top artists to retrieve for user
}
