# API Keys/Credentials get stored here
from envparse import env

# Spotify Definitions
SPOTIFY_API_URL = env.str('MTDJ_SPOTIFY_API_URL', default='https://api.spotify.com/v1')
SPOTIFY_AUTH_URL = env.str('MTDJ_SPOTIFY_API_URL', default='https://accounts.spotify.com/api/token')
SPOTIFY_CLIENT_ID = env.str('MTDJ_SPOTIFY_CLIENT_ID', default='__spotify_client_id_not_set__')
SPOTIFY_SECRET_KEY = env.str('MTDJ_SPOTIFY_SECRET_KEY', default='__spotify_secret_key_not_set__')
SPOTIFY_CATEGORIES = env.list('MTDJ_SPOTIFY_CATEGORIES', default=['hiphop', 'rock', 'alternative'])
SPOTIFY_MAX_SONGS_FROM_LIST = env.int('MTDJ_SPOTIFY_MAX_SONGS_FROM_LIST', default=10)
SPOTIFY_MAX_SONGS_FROM_CATEGORY = env.int('MTDJ_SPOTIFY_MAX_SONGS_FROM_CATEGORY', default=20)
