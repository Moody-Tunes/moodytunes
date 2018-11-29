# moodytunes
The REAL Pandora of emotions

## Setup
Install python3 virtual environment

`sudo apt-get install python3-venv  # Linux based systems`

`brew install python3-venv  # Mac base systems`

Setup python3 virtual environment and activate. You might need to update the `pip` package manager in a newly created
virtual environment.

```
python3 -m venv venv
source venv/bin/activate
(venv) pip install --upgrade pip
```

Install dependencies.

`(venv) pip install -r requirements/dev.text`


## Handy Tips/Tricks
You can start the development server by using the Django `runserver` command. By default this runs on 127.0.0.1:8000

`python manage.py runserver`

You can load test songs into your database by loading the fixture file in the tunes app.
You will need to run the migrations first to create the tables.

```
python manage.py migrate
python manage.py loaddata apps/tunes/fixtures/Initial_Songs.json
```

You can run a Django shell with all the project's model already imported with shell_plus.

`python manage.py shell_plus`

You can run unit tests using tox. This will invoke the Django test runner with the settings we use for running unit tests.

`tox`

Log files are written to the files defined by the `DJANGO_LOG_APP_FILENAME` and `DJANGO_LOG_ERROR_FILENAME` environment variables.
By default they go to `dev_app.log` and `dev_err.log` in the project root directory.

To use logging in your module import `logging`, get a logger, and log away!
```python
import logging

logger = logging.getLogger(__name__)

logger.debug('Hello world!')  # Only prints to the console in local development
logger.info('I saw 14,000,605 futures')
logger.warning('Mr Stark I dont feel so good')
logger.critical('Really? Tears?')
logger.error('You should have gone for the head')
```
