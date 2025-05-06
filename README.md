# Loxberry Plugin: Consumption Prediction

This plugin is designed to predict and manage energy consumption using machine learning models. It collects data via MQTT, stores it in an SQLite database, and provides a web interface to view consumption and prediction data.

## Features
- **Data Collection**: Collects energy consumption data via MQTT.
- **Predictions**: Uses machine learning to predict future energy consumption.
- **Web Interface**: Provides a user-friendly interface to view data and predictions.
- **Automation**: Daily predictions and weekly model training via cron jobs.

## Installation

1. **Download the Plugin**  
   You can directly install the plugin in Loxberry using the following link:  
   https://github.com/Q-Home/ConsumptionPredictionPlugin/archive/refs/tags/v0.0.2.zip
   

2. **Upload to Loxberry**  
   Alternatively, download the plugin manually from the link above and upload it via the Loxberry interface under **Plugins > Install Plugin**.

3. **Post-Installation Script**  
   During installation, the post-installation script ensures all required Python packages are installed and the SQLite database is set up correctly.

4. **MQTT Configuration**  
   Ensure your MQTT broker is running and configured with the following settings:
   - **Broker**: `localhost`
   - **Port**: `1883`
   - **Username**: `loxberry`
   - **Password**: `password`
   - **Topic**: `home/energy/consumption`

5. **Cron Jobs**  
   The plugin automatically configures cron jobs for daily predictions and weekly model training:
   - Predictions: Daily at 00:05
   - Model Training: Weekly on Sunday at 02:00

6. **Web Interface**  
   After installation, access the web interface via the Loxberry dashboard under **Plugins > Consumption Prediction**. Here you can:
   - View current energy consumption.
   - View predictions for future consumption.
   - Manually train the model or run predictions.

## Requirements
- Loxberry version 1.4.3 or higher.
- Python 3 with the following packages:
  - `pandas`
  - `scikit-learn`
  - `paho-mqtt`
  - `joblib`
  - `numpy`

