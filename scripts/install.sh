#! /bin/bash
# moodytunes install script
# Works on UNIX-style systems

function check_for_error {
    # Check if last command succeeded. If it did not, print message passed
    # as argument to function.

    if [[ ! $? -eq 0 ]]
    then
        echo $1 >&2
        exit 1
       fi

}


PROJECT_PYTHON_VERSION="Python 3.5.2"
VIRTUAL_ENV_FILE="venv/bin/activate"

echo "Updating package list. Your password might be required..."
sudo apt-get update > /dev/null

python_version=$(python3 -V)

if [[ ! $python_version = $PROJECT_PYTHON_VERSION ]]
then
    echo "Installing $PROJECT_PYTHON_VERSION"
    sudo apt-get install python3.5 -y > /dev/null
fi

check_for_error "ERROR: Failed to install python3.5"

# Check if python3 venv is installed
python3.5 -m venv venv > /dev/null

if [[ $? -eq 1 ]]
then
	echo "Installing python3 virtualenv..."
	sudo apt-get install python3.5-venv -y > /dev/null
fi

check_for_error "ERROR: Failed to install python3.5-venv"

if [[ ! -d venv ]]
then
	echo "Creating virtual environment..."
	python3.5 -m venv venv
fi

echo "Activating python virtual environment..."
. $VIRTUAL_ENV_FILE

check_for_error "ERROR: Failed to create virtual environment"

pip3 install --upgrade pip
pip3 install -r requirements/dev.txt

check_for_error "ERROR: Failed to install dependencies"

echo "Setting up Django project..."
python manage.py migrate
python manage.py loaddata apps/tunes/fixtures/Initial_Songs.json

check_for_error "ERROR: Failed to start moodytunes Django application"

echo "Finished installing mtdj!"
echo "Enter the command 'source venv/bin/activate' to work in the created virtual environment"
