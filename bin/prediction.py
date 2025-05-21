#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import joblib
from datetime import datetime, timedelta
import numpy as np
import paho.mqtt.client as mqtt
import time
import os
import sys
import json
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# ---------------- Load Settings ----------------
# Path to your JSON file
file_path = '/opt/loxberry/data/plugins/consumption_prediction/settings.json'

# Load JSON data into a Python dictionary
with open(file_path, 'r') as file:
    settings = json.load(file)

# Now `settings` is a dictionary with all your JSON values
print(settings)


# ---------------- Logging Setup ----------------
LOGFILE = "/opt/loxberry/data/plugins/consumption_prediction/prediction.log"

def log(msg):
    os.makedirs(os.path.dirname(LOGFILE), exist_ok=True)
    with open(LOGFILE, "a") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

# ---------------- MQTT Configuration ----------------
MQTT_BROKER = settings['mqtt_broker']
MQTT_PORT = int(settings['mqtt_port'])
MQTT_USERNAME = settings['mqtt_username']
MQTT_PASSWORD = settings['mqtt_password']
MQTT_TOPIC = settings['mqtt_topic_prediction']

log("MQTT settings loaded.")

# ---------------- InfluxDB Configuration ----------------
INFLUX_URL = "http://localhost:8086"
INFLUX_ORG = "Q-Home"
INFLUX_BUCKET = "Energy-prediction"
TOKEN_FILE = "/opt/loxberry/data/plugins/consumption_prediction/.influx_token"

try:
    with open(TOKEN_FILE, "r") as f:
        INFLUX_TOKEN = f.read().strip()
except FileNotFoundError:
    log(f"Token file not found: {TOKEN_FILE}")
    sys.exit(1)

# ---------------- Load Prediction Model ----------------
model_path = "/opt/loxberry/data/plugins/consumption_prediction/energy_model.pkl"
if not os.path.exists(model_path):
    log("Model file not found. Please run train_model.py first.")
    sys.exit(1)

model = joblib.load(model_path)
log("Loaded energy consumption prediction model.")

# ---------------- InfluxDB Client ----------------
client_influx = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
query_api = client_influx.query_api()
write_api = client_influx.write_api(write_options=SYNCHRONOUS)
log("Connected to InfluxDB.")

# ---------------- Query Last 48 Hours ----------------
query = f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: -48h)
  |> filter(fn: (r) => r._measurement == "energy_consumption" and r._field == "consumption_kwh")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
  |> yield(name: "mean")
'''
result = query_api.query(org=INFLUX_ORG, query=query)

# ---------------- Parse Query Results ----------------
records = []
for table in result:
    for record in table.records:
        records.append({
            "datetime": record.get_time(),
            "consumption_kwh": record.get_value()
        })

if not records:
    log("No data returned from InfluxDB for the last 48h.")
    sys.exit(1)

log(f"Retrieved {len(records)} records from InfluxDB.")

# ---------------- Prepare Data ----------------
data = pd.DataFrame(records)
data['datetime'] = pd.to_datetime(data['datetime'])  # Explicitly convert datetime column

latest = data.set_index('datetime').resample('h').mean().ffill()
latest = latest[-48:]

# ---------------- Generate Features ----------------
#start at the beginning of the current hour
#start_time = datetime.now().replace(minute=0, second=0, microsecond=0)
#prediction_hours = [start_time + timedelta(hours=i) for i in range(24)]

# Start at midnight of the next day
tomorrow = datetime.now().date() + timedelta(days=1)
start_time = datetime.combine(tomorrow, datetime.min.time())  # 00:00:00 next day
prediction_hours = [start_time + timedelta(hours=i) for i in range(24)]  # 00:00 to 23:00


prediction_data = pd.DataFrame({
    'datetime': prediction_hours,
    'hour': [dt.hour for dt in prediction_hours],
    'day_of_week': [dt.weekday() for dt in prediction_hours],
    'day': [dt.day for dt in prediction_hours],
    'month': [dt.month for dt in prediction_hours],
    'year': [dt.year for dt in prediction_hours],
})

prediction_data['lag_1h'] = latest['consumption_kwh'].iloc[-1]
prediction_data['lag_24h'] = latest['consumption_kwh'].iloc[-24]

# ---------------- Run Prediction ----------------
X_pred = prediction_data[['hour', 'day_of_week', 'day', 'month', 'year', 'lag_1h', 'lag_24h']]
predictions = model.predict(X_pred)
prediction_data['predicted_kwh'] = predictions

log("Hourly predictions computed.")

# ---------------- Log Predictions to File ----------------
with open(LOGFILE, "a") as logfile:
    logfile.write(f"Hourly prediction starting {start_time.strftime('%Y-%m-%d %H:%M:%S')}:\n")
    for dt, pred in zip(prediction_data['datetime'], predictions):
        logfile.write(f"{dt.strftime('%Y-%m-%d %H:%M:%S')} - {pred:.2f} kWh\n")
    logfile.write("-" * 40 + "\n")

log("Predictions logged to prediction.log.")

# ---------------- Write Predictions to InfluxDB ----------------
for dt, pred in zip(prediction_data['datetime'], predictions):
    point = (
        Point("predictions")
        .field("predicted_kwh", float(pred))
        .time(dt)
    )
    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

log("Predictions written to InfluxDB.")

# ---------------- Publish Predictions via MQTT ----------------
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.connect(MQTT_BROKER, MQTT_PORT, 60)

payload = {
    "timestamp": start_time.strftime('%Y-%m-%d %H:%M:%S'),
    "predictions": [
        {"datetime": dt.strftime('%Y-%m-%d %H:%M:%S'), "kwh": round(pred, 2)}
        for dt, pred in zip(prediction_data['datetime'], predictions)
    ]
}

client.publish(MQTT_TOPIC, json.dumps(payload))
client.disconnect()

log("Predictions sent to MQTT.")
