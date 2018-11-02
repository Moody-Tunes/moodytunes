### Test specfic settings

from .common import *

# Don't write to the console during unit test
LOGGING['root']['handlers'] = ['app_file', 'error_file']
