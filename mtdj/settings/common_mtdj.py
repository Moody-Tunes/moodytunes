import tempfile

from envparse import env


DATABASE_BACKUPS_PATH = env.str('MTDJ_DATABASE_BACKUPS_PATH', default=tempfile.gettempdir())
DATABASE_BACKUP_TARGETS = [
    'accounts.MoodyUser',
    'accounts.UserEmotion',
    'accounts.UserSongVote',
    'tunes.Emotion',
    'tunes.Song',
]

IMAGE_FILE_UPLOAD_PATH = env.str('MTDJ_IMAGE_FILE_UPLOAD_PATH', default=tempfile.gettempdir())

BROWSE_DEFAULT_JITTER = env.float('MTDJ_BROWSE_DEFAULT_JITTER', default=0.05)
BROWSE_DEFAULT_LIMIT = env.int('MTDJ_BROWSE_DEFAULT_LIMIT', default=9)
BROWSE_PLAYLIST_STRATEGIES = ['energy', 'valence', 'danceability']

CANDIDATE_BATCH_SIZE_FOR_USER_EMOTION_ATTRIBUTES_UPDATE = 15

CREATE_USER_EMOTION_RECORDS_SIGNAL_UID = 'user_post_save_create_useremotion_records'
UPDATE_USER_EMOTION_ATTRIBUTES_SIGNAL_UID = 'user_song_vote_post_save_update_useremotion_attributes'
UPDATE_SPOTIFY_DATA_TOP_ARTISTS_SIGNAL_UID = 'spotify_user_auth_post_save_update_top_artist'
ADD_SPOTIFY_DATA_TOP_ARTISTS_SIGNAL_UID = 'spotify_auth_post_save_add_spotify_top_artists'
LOG_MOODY_USER_FAILED_LOGIN_SIGNAL_UID = 'moody_user_failed_login'
