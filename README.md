# ConsumptionPredictionPlugin

A LoxBerry plugin for predicting energy consumption using data from your Loxone Smart Home system.

## Features

- Predicts future energy consumption based on historical data.
- Integrates seamlessly with Loxone Miniserver.
- Provides easy-to-read charts and reports.
- Customizable prediction intervals.

## Requirements

- **LoxBerry**: Installed and running on your device.
- **Loxone Miniserver**: Required for data collection.
- **Loxone Web Services**: Enable HTTP API access on your Miniserver.
- **User Account**: A Loxone user with permission to access energy meter data.

## Loxone Setup

1. **Enable Web Services**  
   In Loxone Config, go to *Miniserver* > *Network* and ensure HTTP API access is enabled.

2. **Create a User**  
   Create a dedicated user for the plugin with read access to energy meter data.

3. **Find UUIDs**  
   Locate the UUIDs of your energy meters in Loxone Config or via the API.

## Installation

1. Download and install the plugin via the LoxBerry Plugin Manager.  
2. Configure the plugin with your Loxone Miniserver IP, credentials, MQTT topics, etc. in the settings page.  
3. Save and restart the plugin.

## Usage

- Access the plugin via the LoxBerry web interface.  
- Links to InfluxDB and Grafana (a dashboard is not automatically on there).  
- Adjust settings as needed.  
- View log files.

## In Loxone

### Data Sending

You need to send the consumption data from Loxone to the LoxBerry using the MQTT topics set in the settings page.  

To receive the prediction data in Loxone, add virtual inputs.

**For consumption prediction:**

- pred_0004  
- pred_0408  
- pred_0812  
- pred_1216  
- pred_1620  
- pred_2024  

**For solar prediction:**

- pred_sol_0004  
- pred_sol_0408  
- pred_sol_0812  
- pred_sol_1216  
- pred_sol_1620  
- pred_sol_2024  

---

## Fixing "Address Already in Use" Errors in Docker

When running `docker compose up`, you might see an error like:
Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint influxdb (28a0353192673f35a159632898d30967f2ace53d3f7721d3eef99ccb32afc3c9): failed to bind host port for 0.0.0.0:8086:172.20.0.10:8086/tcp: address already in use

This means another process is already using the port Docker is trying to bind.

### Steps to Fix

```bash
# 1. Check what’s using the port
sudo lsof -i :<port_number>
# or
sudo netstat -tulpn | grep <port_number>

# 2. If it’s another Docker container
docker ps | grep <port_number>
docker stop <container_id>
docker compose up -d

# 3. If it’s a local service
sudo systemctl stop <service_name>
# Example:
sudo systemctl stop influxdb

# 4. If you can’t stop the existing service, edit docker-compose.yml:
# ports:
#   - "NEW_HOST_PORT:CONTAINER_PORT"
# Example:
# ports:
#   - "8087:8086"

# 5. Restart Docker Compose
docker compose down
docker compose up -d
