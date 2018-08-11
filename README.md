# moodytunes
The REAL Pandora of emotions

## Setup
Install python3 virtual environment

`sudo apt-get install python3-venv  # Linux based systems`

`brew install python3-venv  # Mac base systems`

Setup python3 virtual environment and activate

`python3 -m venv venv`

`source venv/bin/activate`

Install dependencies

`pip install -r requirements/dev.text`


## Handy Commands
1) You can run a Django shell with all the project's model already imported with shell_plus

`python manage.py shell_plus`

2) You can run unit tests using tox

`tox -r`

3) Log files are written to the files defined by the `DJANGO_LOG_APP_FILENAME` and `DJANGO_LOG_ERROR_FILENAME` environment variables.
By default they go to `dev_app.log` and `dev_err.log` in the project root directory.

To use logging in your module import `logging`, get a logger, and log away!
```python
import logging

from libs.moody_logging import format_module_name_with_project_prefix

module_name = format_module_name_with_project_prefix(__name__)
logger = logging.getLogger(module_name)

logger.debug('Hello world!')  # Only prints to the console in local development
logger.info('I saw 14,000,605 futures')
logger.warning('Mr Stark I dont feel so good')
logger.critical('Really? Tears?')
logger.error('You should have gone for the head')
```
