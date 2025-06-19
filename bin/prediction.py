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

file_path = '/opt/loxberry/data/plugins/consumption_prediction/settings.json'
with open(file_path, 'r') as file:
    settings = json.load(file)

LOGFILE = "/opt/loxberry/data/plugins/consumption_prediction/prediction.log"
def log(msg):
    os.makedirs(os.path.dirname(LOGFILE), exist_ok=True)
    with open(LOGFILE, "a") as f:
        f.write(f"[{datetime.now()}] [CONSUMPTION] {msg}\n")
    print(f"[{datetime.now()}] [CONSUMPTION] {msg}")

# MQTT
MQTT_BROKER = settings['mqtt_broker']
MQTT_PORT = int(settings['mqtt_port'])
MQTT_USERNAME = settings['mqtt_username']
MQTT_PASSWORD = settings['mqtt_password']
MQTT_TOPIC = settings['mqtt_topic_prediction']

# InfluxDB
INFLUX_URL = "http://localhost:8086"
INFLUX_ORG = "Q-Home"
INFLUX_BUCKET = "Energy-prediction"
TOKEN_FILE = "/opt/loxberry/data/plugins/consumption_prediction/.influx_token"

try:
    with open(TOKEN_FILE, "r") as f:
        INFLUX_TOKEN = f.read().strip()
except Exception as e:
    log(f"Failed to read InfluxDB token: {e}")
    sys.exit(1)

# Load Model
model_path = "/opt/loxberry/data/plugins/consumption_prediction/energy_model.pkl"
if not os.path.exists(model_path):
    log("Model file not found.")
    sys.exit(1)

try:
    model = joblib.load(model_path)
except Exception as e:
    log(f"Error loading model: {e}")
    sys.exit(1)

# Connect Influx
try:
    client_influx = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    query_api = client_influx.query_api()
    write_api = client_influx.write_api(write_options=SYNCHRONOUS)
except Exception as e:
    log(f"InfluxDB connection failed: {e}")
    sys.exit(1)

# Query last 48h
query = f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: -48h)
  |> filter(fn: (r) => r._measurement == "energy_consumption" and r._field == "consumption_kwh")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
  |> yield(name: "mean")
'''
try:
    result = query_api.query(org=INFLUX_ORG, query=query)
except Exception as e:
    log(f"Error querying InfluxDB: {e}")
    sys.exit(1)

# Parse results
records = []
for table in result:
    for record in table.records:
        records.append({
            "datetime": record.get_time(),
            "consumption_kwh": record.get_value()
        })

if not records:
    log("No data received from InfluxDB.")
    sys.exit(1)

# Prepare history
data = pd.DataFrame(records)
data['datetime'] = pd.to_datetime(data['datetime'])
latest = data.set_index('datetime').resample('h').mean().ffill()
latest = latest[-48:]

# Prepare future timestamps
tomorrow = datetime.now().date() + timedelta(days=0)
start_time = datetime.combine(tomorrow, datetime.min.time())
prediction_hours = [start_time + timedelta(hours=i) for i in range(24)]

prediction_data = pd.DataFrame({
    'datetime': prediction_hours,
    'hour': [dt.hour for dt in prediction_hours],
    'day_of_week': [dt.weekday() for dt in prediction_hours],
    'day': [dt.day for dt in prediction_hours],
    'month': [dt.month for dt in prediction_hours],
    'year': [dt.year for dt in prediction_hours],
    'is_weekend': [1 if dt.weekday() >= 5 else 0 for dt in prediction_hours],
})

# Recursive prediction
last_1h = latest['consumption_kwh'].iloc[-1]
last_2h = latest['consumption_kwh'].iloc[-2]
last_3h = latest['consumption_kwh'].iloc[-3]
lag_24h = latest['consumption_kwh'].iloc[-24]

predictions = []
for i in range(24):
    row = prediction_data.iloc[i]

    row_data = {
        'hour': row['hour'],
        'day_of_week': row['day_of_week'],
        'day': row['day'],
        'month': row['month'],
        'year': row['year'],
        'is_weekend': row['is_weekend'],
        'lag_1h': last_1h,
        'lag_2h': last_2h,
        'lag_3h': last_3h,
        'lag_24h': lag_24h,
        'rolling_mean_3h': np.mean([last_1h, last_2h, last_3h]),
        'rolling_mean_6h': np.mean([last_1h, last_2h, last_3h, lag_24h, lag_24h, lag_24h])
    }

    X_pred = pd.DataFrame([row_data])
    pred = model.predict(X_pred)[0]
    predictions.append(pred)

    # Update rolling context
    last_3h, last_2h, last_1h = last_2h, last_1h, pred

prediction_data['predicted_kwh'] = predictions

# Log to file
with open(LOGFILE, "a") as logfile:
    logfile.write(f"Hourly prediction for {start_time}:\n")
    for dt, pred in zip(prediction_data['datetime'], predictions):
        logfile.write(f"{dt} - {pred:.2f} kWh\n")
    logfile.write("-" * 40 + "\n")
log("Predictions logged.")

# Write to InfluxDB
for dt, pred in zip(prediction_data['datetime'], predictions):
    point = Point("predictions").field("predicted_kwh", float(pred)).time(dt)
    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
log("Predictions written to InfluxDB.")

# MQTT
try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    payload = {
        "timestamp": start_time.strftime('%Y-%m-%d %H:%M:%S'),
        "predictions_test": [
            {"datetime": dt.strftime('%Y-%m-%d %H:%M:%S'), "kwh": round(pred, 2)}
            for dt, pred in zip(prediction_data['datetime'], predictions)
        ]
    }

    client.publish(MQTT_TOPIC, json.dumps(payload))
    client.disconnect()

    log("Predictions sent via MQTT.")
except Exception as e:
    log(f"Error publishing to MQTT: {e}")
