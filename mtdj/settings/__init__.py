import os
from envparse import env

# Load env file
env_file = os.environ.get('MTDJ_ENV_FILE', 'dev.env')
env.read_envfile(env_file)

ENV = env.str('ENV', default='dev')

from .common import *
