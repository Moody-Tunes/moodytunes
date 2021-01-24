from envparse import env
from spotify_client.config import Config


# Spotify OAuth scope constants
SPOTIFY_PLAYLIST_MODIFY_SCOPE = 'playlist-modify-public'
SPOTIFY_TOP_ARTIST_READ_SCOPE = 'user-top-read'
SPOTIFY_UPLOAD_PLAYLIST_IMAGE = 'ugc-image-upload'

# Spotify Definitions
SPOTIFY = {
    'client_id': env.str('MTDJ_SPOTIFY_CLIENT_ID', default='__spotify_client_id_not_set__'),
    'secret_key': env.str('MTDJ_SPOTIFY_SECRET_KEY', default='__spotify_secret_key_not_set__'),
    'categories': env.list('MTDJ_SPOTIFY_CATEGORIES', default=['hiphop', 'rock', 'chill']),
    'auth_redirect_uri': env.str('MTDJ_SPOTIFY_REDIRECT_URI', default='https://moodytunes.vm/spotify/callback/'),
    'auth_user_token_timeout': 60 * 60,  # User auth token is good for one hour
    'auth_user_scopes': [SPOTIFY_PLAYLIST_MODIFY_SCOPE, SPOTIFY_TOP_ARTIST_READ_SCOPE, SPOTIFY_UPLOAD_PLAYLIST_IMAGE],
    'max_top_artists': env.int('MTDJ_SPOTIFY_MAX_TOP_ARTISTS', default=50),
    'session_state_length': env.int('MTDJ_SPOTIFY_AUTH_STATE_LENGTH', default=48),
}

# Configure SpotifyClient with authentication credentials
Config.configure(SPOTIFY['client_id'], SPOTIFY['secret_key'])
