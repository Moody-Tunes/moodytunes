# moodytunes
The REAL Pandora of emotions

This is for a test

## Setup

We use Vagrant and ansible to manage building and provisioning virtual machines. This ensures that we can easily build
new hosts for our producion environment, as well as develop in a similar environment to the one we'll deploy mtdj. See
our [cradle](https://github.com/Moody-Tunes/cradle#cradle) repository for how to get an instance of mtdj setup and running.

We also use [pre-commit](https://pre-commit.com/) for running hooks during git commits. This will help immensely with
developer workflow by running linters, checkers, and other tools when you make commits. To install pre-commit, create a
virtual environment and install pre-commit:

```shell script
virtualenv -p $(which python3) venv
source venv/bin/activate
(venv) pip install pre-commit
```

Next, install the pre-commit packages we use in our project:

```shell script
(venv) pre-commit install
```

This should run the pre-commit hooks when you make a commit to the moodytunes repository.

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

We use the [coverage](https://coverage.readthedocs.io/en/v4.5.x/) package to report how much of our codebase has unit
test coverage. After running the tests using tox, you can see a report of the current test coverage by running

`coverage report`

after tox has finished its run. If you would like to see a detailed output of the coverage (like what exact lines were hit) the
pytest coverage plugin we use generates HTML files of code test coverage after a test run. These files are available in
the `htmlcov` directory in the project. Open the index.html file in any browser of your choice to view the source files
for the project, their coverage percentage, and what lines have (or have not) been tested.

NOTE: Your build will fail and any pull request rejected if the total coverage is less than 80% after the Travis build
is finished. If you *need* to circumvent this, you can cover any code that doesn't need to be tested with pragmas:

```python
if settings.DEBUG:  # pragma: no cover
    print('Not necessary to test...')
```

### Logging

Log files are written to the directory defined by the `DJANGO_APP_LOG_DIR` environment variable.
By default they go to `application.log` and `error.log` in the directory perscribed by `DJANGO_APP_LOG_DIR`.

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

### Static Files

Static files are served through the nginx webserver in our configuration. When you make changes to static files during
development, they should automatically be picked up by the [django-compressor](https://github.com/django-compressor/django-compressor)
plugin that will regenerate the static file served to the frontend. If you add a new static file to a template, you may
need to run

`./manage.py collectstatic`

to notify Django that there is a new static file to be collected. Our static files live in the `static/` directory located
in the project root. Please namespace the file under the appropriate app name. For example, if you are adding a LESS
file in a template that lives in the mooydytunes app, please place the file in the `static/moodytunes/less/` directory

### Running Daemon Processes

We use `systemd` for managing the processes needed for running the site. We currently have configurations set up for gunicorn, celery, and celery_beat to run through `systemctl` in the background. To start the daemon, enter

`sudo systemctl start {process_name}`

You can verify the status through the command by entering

`sudo systemctl status {process_name}`

To halt the daemon, enter

`sudo systemctl stop {process_name}`
