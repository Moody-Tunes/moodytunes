#! /bin/bash

# moodytunes install script

# Check if python3 venv is insstalled
python3 -m venv venv > /dev/null

if [ $? -eq 1 ]
then
	echo "Installing python3 virtualenv..."
	sudo apt-get install python3.5-venv -y > /dev/null
fi

if [ ! -d venv ]
then
	echo "Creating virtual environment..."
	python3 -m venv venv
fi

echo "Activating python virtual environment..."
. venv/bin/activate

pip3 install --upgrade pip
pip3 install -r requirements/dev.txt

echo "Setting up Django project..."
python manage.py migrate
python loaddata apps/tunes/fixtures/Initial_Songs.json

echo "Finished installing mtdj!"
echo "In the future, execute 'source venv/bin/activate' to work in the created virtual environment"

