# moodytunes
The REAL Pandora of emotions

## Setup

If you happen to be running Linux Mint 18.3, you can run scripts/install.sh to install the proper packages to run
moodytunes on your machine

`bash scripts/install.sh`

This will install python3.5 and python3.5-venv on your system, as well as create a virtual environment, install the
needed dependencies, and start your moodytunes application. If you are running a different OS, follow the steps below

Install python3 virtual environment

`sudo apt-get install python3.5-venv  # Linux based systems`

`brew install python3.5-venv  # Mac base systems`

Setup python3 virtual environment and activate. You should to update the `pip` package manager in a newly created
virtual environment.

```
python3.5 -m venv venv
source venv/bin/activate
(venv) pip install --upgrade pip
```

Run the needed migrations and load the sample song data into your database. This will create a db.sqlite3 file in the
project directory to act as your local database

```
python manage.py migrate
python manage.py loaddata apps/tunes/fixtures/Initial_Songs.json
```

Install dependencies.

`(venv) pip install -r requirements/dev.text`


## Handy Tips/Tricks
You can start the development server by using the Django `runserver` command. By default this runs on 127.0.0.1:8000

`python manage.py runserver`

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
