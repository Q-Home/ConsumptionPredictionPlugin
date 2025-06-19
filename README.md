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

1. **Enable Web Services**:  
    In Loxone Config, go to *Miniserver* > *Network* and ensure HTTP API access is enabled.

2. **Create a User**:  
    Create a dedicated user for the plugin with read access to energy meter data.

3. **Find UUIDs**:  
    Locate the UUIDs of your energy meters in Loxone Config or via the API.

## Installation

1. Download and install the plugin via the LoxBerry Plugin Manager.
2. Configure the plugin with your Loxone Miniserver IP, credentials, MQTT-topics etc. in the settings page
3. Save and restart the plugin.

## Usage

- Access the plugin via the LoxBerry web interface.
- Links to InfluxDB and grafana(a dashboard is not automatically on there)
- Adjust settings as needed.
- View log files

## In Loxone

### data sending

You need to send the consumption data from Loxone to the loxberry  using mqtt topics set in the settings page.
To receive the prediction data in Loxone, add virtual inputs:
For consumption prediction:

- pred_0004
- pred_0408
- pred_0812
- pred_1216
- pred_1620
- pred_2024

For solar prediction:

- pred_sol_0004
- pred_sol_0408
- pred_sol_0812
- pred_sol_1216
- pred_sol_1620
- pred_sol_2024

