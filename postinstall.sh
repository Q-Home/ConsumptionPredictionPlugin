#!/bin/bash

# Shell script which is executed by bash *AFTER* complete installation is done
# (but *BEFORE* postupdate). Use with caution and remember, that all systems may
# be different!
#
# Exit code must be 0 if executed successfull.
# Exit code 1 gives a warning but continues installation.
# Exit code 2 cancels installation.
#
# Will be executed as user "loxberry".
#
# You can use all vars from /etc/environment in this script.
#
# We add 5 additional arguments when executing this script:
# command <TEMPFOLDER> <NAME> <FOLDER> <VERSION> <BASEFOLDER>
#
# For logging, print to STDOUT. You can use the following tags for showing
# different colorized information during plugin installation:
#
# <OK> This was ok!"
# <INFO> This is just for your information."
# <WARNING> This is a warning!"
# <ERROR> This is an error!"
# <FAIL> This is a fail!"

# To use important variables from command line use the following code:
COMMAND=$0    # Zero argument is shell command
PTEMPDIR=$1   # First argument is temp folder during install
PSHNAME=$2    # Second argument is Plugin-Name for scipts etc.
PDIR=$3       # Third argument is Plugin installation folder
PVERSION=$4   # Forth argument is Plugin version
#LBHOMEDIR=$5 # Comes from /etc/environment now. Fifth argument is
# Base folder of LoxBerry
PTEMPPATH=$6  # Sixth argument is full temp path during install (see also $1)

# Combine them with /etc/environment
PHTMLAUTH=$LBHOMEDIR/webfrontend/htmlauth/plugins/$PDIR
PHTML=$LBPHTML/$PDIR
PTEMPL=$LBPTEMPL/$PDIR
PDATA=$LBPDATA/$PDIR
PLOGS=$LBPLOG/$PDIR # Note! This is stored on a Ramdisk now!
PCONFIG=$LBPCONFIG/$PDIR
PSBIN=$LBPSBIN/$PDIR
PBIN=$LBPBIN/$PDIR

/usr/bin/python3 -m pip install --quiet --no-cache-dir paho-mqtt

DB="/opt/loxberry/data/plugins/consumption_prediction/energy_data.sqlite"

echo "Ensuring SQLite DB schema exists..."

# Create consumption_data table if it doesn't exist
sqlite3 /opt/loxberry/data/plugins/consumption_prediction/energy_data.sqlite "CREATE TABLE IF NOT EXISTS consumption_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    datetime TEXT NOT NULL,
    consumption_kwh REAL NOT NULL
);"

# Create predictions table if it doesn't exist
sqlite3 /opt/loxberry/data/plugins/consumption_prediction/energy_data.sqlite "CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    datetime TEXT NOT NULL,
    predicted_kwh REAL NOT NULL
);"

# Insert 50 rows of test data into the consumption_data table
# Insert 50 rows of test data into the consumption_data table
# echo "Inserting test data into consumption_data..."

# for i in $(seq 1 50); do
#     # Generate random date within the last 7 days
#     datetime=$(date -d "$((RANDOM % 7)) days ago" "+%Y-%m-%d %H:%M:%S")

#     # Generate random consumption value between 0.5 kWh and 10 kWh
#     consumption_kwh=$(echo "scale=2; $RANDOM % 950 / 100" | bc)

#     # Insert the generated data into the database
#     sqlite3 $DB "INSERT INTO consumption_data (datetime, consumption_kwh) VALUES ('$datetime', '$consumption_kwh');"
# done

# echo "Test data inserted successfully.


#install python packages
# Ensure the system has the latest package information
sudo apt-get update

# Install Python3 and pip3 if not already installed
sudo apt-get install -y python3 python3-pip

# Install the required packages for your script
pip3 install pandas scikit-learn matplotlib numpy sqlite3, paho-mqtt, joblib

# Check installed versions
python3 -m pip show pandas scikit-learn matplotlib numpy sqlite3

#run python script in the background
nohup python3 /opt/loxberry/bin/plugins/consumption_prediction/mqtt_to_db.py > /dev/null 2>&1 &



# Exit with Status 0
exit 0
