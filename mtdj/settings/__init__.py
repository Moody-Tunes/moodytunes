import os
import sys

from envparse import env

# Load env file
env_file = os.environ.get('MTDJ_ENV_FILE', '.dev')
env.read_envfile(env_file)

ENV = env.str('ENV', default='dev')
PROJECT_PREFIX = 'mtdj'

# Add apps/ and libs/ directory to Python path
parent_dir = os.path.dirname  # For better readability
BASE_DIR = parent_dir(parent_dir(parent_dir(os.path.abspath(__file__))))
APPS_DIR = '{}/{}'.format(BASE_DIR, 'apps')
LIBS_DIR = '{}/{}'.format(BASE_DIR, 'libs')

sys.path.append(APPS_DIR)
sys.path.append(LIBS_DIR)

if ENV == 'dev':
    try:
        from .local_personal import *
    except ImportError:
        from .local import *
else:
    from .common import *
