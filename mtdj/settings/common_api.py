# API Keys/Credentials get stored here
from envparse import env

# Spotify Definitions
SPOTIFY_API_URL = 'https://api.spotify.com/v1'
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_CLIENT_ID = env.str('MTDJ_SPOTIFY_CLIENT_ID', default='__spotify_client_id_not_set__')
SPOTIFY_SECRET_KEY = env.str('MTDJ_SPOTIFY_SECRET_KEY', default='__spotify_secret_key_not_set__')
