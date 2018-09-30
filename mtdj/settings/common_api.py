# API Keys/Credentials get stored here
from envparse import env

# Spotify Definitions
SPOTIFY = {
    'api_url': env.str('MTDJ_SPOTIFY_API_URL', default='https://api.spotify.com/v1'),
    'auth_url': env.str('MTDJ_SPOTIFY_API_URL', default='https://accounts.spotify.com/api/token'),
    'client_id': env.str('MTDJ_SPOTIFY_CLIENT_ID', default='__spotify_client_id_not_set__'),
    'secret_key': env.str('MTDJ_SPOTIFY_SECRET_KEY', default='__spotify_secret_key_not_set__'),
    'categories': env.list('MTDJ_SPOTIFY_CATEGORIES', default=['hiphop', 'rock', 'chill']),
    'max_songs_from_list': env.int('MTDJ_SPOTIFY_MAX_SONGS_FROM_LIST', default=10),
    'max_songs_from_category': env.int('MTDJ_SPOTIFY_MAX_SONGS_FROM_CATEGORY', default=20),
    'auth_cache_key': env.str('MTDJ_SPOTIFY_AUTH_CACHE_KEY', default='mtdj:spotify-auth-token'),
    'auth_cache_key_timeout': 60 * 60,  # Authorization token is good for one hour
}
