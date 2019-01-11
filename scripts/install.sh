#! /bin/bash
# moodytunes install script
# Works on UNIX-style systems

PROJECT_PYTHON_VERSION="Python 3.5.2"

# Ensure python3 version is 3.5
python_version=$(python3 -V)

if [[ ! $python_version = $PROJECT_PYTHON_VERSION ]]
then
    echo "Installing $PROJECT_PYTHON_VERSION"
    sudo apt-get install python3.5 -y >/dev/null
fi

# Check if python3 venv is installed
python3.5 -m venv venv > /dev/null

if [[ $? -eq 1 ]]
then
	echo "Installing python3 virtualenv..."
	sudo apt-get install python3.5-venv -y > /dev/null
fi

if [[ ! -d venv ]]
then
	echo "Creating virtual environment..."
	python3.5 -m venv venv
fi

echo "Activating python virtual environment..."
. venv/bin/activate

pip3 install --upgrade pip
pip3 install -r requirements/dev.txt

echo "Setting up Django project..."
python manage.py migrate
python manage.py loaddata apps/tunes/fixtures/Initial_Songs.json

echo "Finished installing mtdj!"
echo "In the future, execute 'source venv/bin/activate' to work in the created virtual environment"

