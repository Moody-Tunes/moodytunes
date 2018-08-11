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
