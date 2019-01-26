# moodytunes
The REAL Pandora of emotions

## Setup

We use Vagrant and ansible to manage building and provisioning virtual machines. This ensures that we can easily build
new hosts for our producion environment, as well as develop in a similar environment to the one we'll deploy mtdj. See
our [cradle](https://github.com/Moody-Tunes/cradle#cradle) repository for how to get an instance of mtdj setup and running.

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
