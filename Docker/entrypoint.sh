#!/bin/sh

# Check if jageocoder dictionary is installed.
DBDIR=`python -m jageocoder get-db-dir`
if [ -n $DBDIR ]; then
	echo -n "Installing Jageocoder dictionary..."
	python -m jageocoder install-dictionary
	echo "done."
fi

# Set up basic geonlp dictionaries
python /tmp/init.py

# Run flask
flask run -h 0.0.0.0 -p 5000
