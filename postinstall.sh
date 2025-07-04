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



LOG_FILE="/tmp/consumption_prediction_postinstall.log"
exec > >(tee -a "$LOG_FILE") 2>&1
echo "Postinstall started at $(date)"

# Install the required packages
sudo apt-get update
pip3 install pandas scikit-learn matplotlib numpy paho-mqtt joblib influxdb-client requests

sudo /opt/loxberry/bin/plugins/consumption_prediction/run_docker_compose.sh

# Wait until InfluxDB is ready (max 60 seconds)
echo "Waiting for InfluxDB to become available..."
for i in {1..60}; do
  if docker exec influxdb curl -s http://localhost:8086/health | grep -q '"status":"pass"'; then
    echo "InfluxDB is ready."
    break
  fi
  sleep 1
done

# Install and configure
sudo /opt/loxberry/bin/plugins/consumption_prediction/create_influxdb_token.sh



# Clean up install scripts
rm /opt/loxberry/bin/plugins/consumption_prediction/install_grafana_influxdb.sh
rm /opt/loxberry/bin/plugins/consumption_prediction/create_influxdb_token.sh
rm /opt/loxberry/bin/plugins/consumption_prediction/run_docker_compose.sh
rm /opt/loxberry/bin/plugins/consumption_prediction/create_grafana_datasource.sh



echo "Postinstall completed at $(date)"
exit 0
