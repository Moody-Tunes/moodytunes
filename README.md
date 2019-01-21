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

Install dependencies.

`(venv) pip install -r requirements/dev.text`

Run the needed migrations and load the sample song data into your database. This will create a db.sqlite3 file in the
project directory to act as your local database

```
python manage.py migrate
python manage.py loaddata apps/tunes/fixtures/Initial_Songs.json
```

## Handy Tips/Tricks

### Django Commands

You can start the development server by using the Django `runserver` command. By default this runs on 127.0.0.1:8000

`python manage.py runserver`

You can run a Django shell with all the project's model already imported with shell_plus.

`python manage.py shell_plus`


### Unit Tests

You can run unit tests using [tox](https://tox.readthedocs.io/en/latest/). This will invoke the Django test runner with the settings we use for running unit tests.

`tox`

If you added packages to the requirements file and need them in your tests, you might need to recreate the tox
virtual environment. You can do this by passing the `--recreate` flag to tox.

`tox -r [--recreate]`

We use the [coverage](https://coverage.readthedocs.io/en/v4.5.x/) pacakge to report how much of our codebase has unit
test coverage. After running the tests using tox, you can see a report of the current coverage by running

`coverage report`

after running tox. If you would like to see a detailed output of the coverage (like what exact lines were hit) you can
generate an HTML report by running

`coverage html`

This will generate a directory in the project root with files corresponding to each code file in the project. Open the
index.html file in any browser of your chouce to view the source files for the project, their coverage percentage, and
what lines have (or have not) been tested.

NOTE: Your build will fail and any pull request rejected if the total coverage is less than 80% after the Travis build
is finished. If you *need* to circumvent this, you can cover any code that doesn't need to be tested with pragmas:

```python
if settings.DEBUG:  # pragma: no cover
    print('Not necessary to test...')
```

### Logging

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
