#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import sqlite3
import joblib
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime, timedelta
import numpy as np
import paho.mqtt.client as mqtt
import time
import os
import sys

# MQTT configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_USERNAME = "loxberry"
MQTT_PASSWORD = "loxberry"
MQTT_TOPIC = "home/energy/predictions"

# Load model
model_path = "/opt/loxberry/data/plugins/consumption_prediction/energy_model.pkl"
if not os.path.exists(model_path):
    print("Model file not found. Please run train_model.py first.")
    sys.exit(1)

model = joblib.load(model_path)

# Connect to database
conn = sqlite3.connect("/opt/loxberry/data/plugins/consumption_prediction/energy_data.sqlite")
data = pd.read_sql_query('SELECT datetime, consumption_kwh FROM consumption_data', conn, parse_dates=['datetime'])

# Basic check
if data.empty or len(data) < 48:
    print("Not enough data for prediction.")
    conn.close()
    sys.exit(1)

# Latest data for lag features
latest = data.set_index('datetime').resample('H').mean().ffill()
latest = latest[-48:]  # last 2 days

# Prepare prediction input for tomorrow
tomorrow = datetime.now() + timedelta(days=1)
prediction_hours = [tomorrow.replace(hour=h, minute=0, second=0, microsecond=0) for h in range(24)]

prediction_data = pd.DataFrame({
    'datetime': prediction_hours,
    'hour': [dt.hour for dt in prediction_hours],
    'day_of_week': [dt.weekday() for dt in prediction_hours],
    'day': [dt.day for dt in prediction_hours],
    'month': [dt.month for dt in prediction_hours],
    'year': [dt.year for dt in prediction_hours],
})

# Estimate lag features based on prior data
prediction_data['lag_1h'] = latest['consumption_kwh'].iloc[-1]
prediction_data['lag_24h'] = latest['consumption_kwh'].iloc[-24]

X_pred = prediction_data[['hour', 'day_of_week', 'day', 'month', 'year', 'lag_1h', 'lag_24h']]
predictions = model.predict(X_pred)
total_kwh = np.sum(predictions)

# Save prediction to log
with open("/opt/loxberry/data/plugins/consumption_prediction/prediction.log", "a") as logfile:
    logfile.write(f"Prediction for {tomorrow.date()}:\n")
    for dt, pred in zip(prediction_hours, predictions):
        logfile.write(f"{dt.strftime('%Y-%m-%d %H:%M:%S')} - {pred:.2f} kWh\n")
    logfile.write(f"Total predicted consumption: {total_kwh:.2f} kWh\n")
    logfile.write("-" * 40 + "\n")

# Save total daily prediction to DB
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS predictions (id INTEGER PRIMARY KEY AUTOINCREMENT, datetime TEXT NOT NULL, predicted_kwh REAL NOT NULL);")
cursor.execute("INSERT INTO predictions (datetime, predicted_kwh) VALUES (?, ?)", (tomorrow, total_kwh))
conn.commit()
conn.close()

# Send to MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.publish(MQTT_TOPIC, str(total_kwh))
client.disconnect()
