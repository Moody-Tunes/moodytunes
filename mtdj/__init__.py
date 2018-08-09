import os
import sys

# Add apps directory to Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS_DIR = '{}/{}'.format(BASE_DIR, 'apps')
LIBS_DIR = '{}/{}'.format(BASE_DIR, 'libs')

sys.path.append(APPS_DIR)
sys.path.append(LIBS_DIR)
