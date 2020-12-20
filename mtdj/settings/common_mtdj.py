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
