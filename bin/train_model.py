#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from influxdb_client import InfluxDBClient
from datetime import datetime
import os

# ---------------- Logging Setup ----------------
LOGFILE = "/opt/loxberry/data/plugins/consumption_prediction/train_model.log"

def log(msg):
    os.makedirs(os.path.dirname(LOGFILE), exist_ok=True)
    with open(LOGFILE, "a") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

# ---------------- Configuration ----------------
TOKEN_FILE = "/opt/loxberry/data/plugins/consumption_prediction/.influx_token"
MODEL_PATH = "/opt/loxberry/data/plugins/consumption_prediction/energy_model.pkl"
INFLUX_URL = "http://localhost:8086"
ORG = "Q-Home"
BUCKET = "Energy-prediction"

log("Starting model training script.")

# ---------------- Token Loading ----------------
try:
    with open(TOKEN_FILE, "r") as f:
        INFLUX_TOKEN = f.read().strip()
    log("InfluxDB token loaded successfully.")
except FileNotFoundError:
    log(f"[error] Token file not found: {TOKEN_FILE}")
    exit(1)

# ---------------- InfluxDB Connection ----------------
try:
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=ORG)
    query_api = client.query_api()
    log("Connected to InfluxDB.")
except Exception as e:
    log(f"[error] Failed to connect to InfluxDB: {e}")
    exit(1)

# ---------------- Data Query ----------------
query = f'''
from(bucket: "{BUCKET}")
|> range(start: -14d)
|> filter(fn: (r) => r["_measurement"] == "energy_consumption" and r["_field"] == "consumption_kwh")
|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
'''

try:
    result = query_api.query_data_frame(org=ORG, query=query)
    log("Data queried from InfluxDB.")
except Exception as e:
    log(f"[error] Failed to query data from InfluxDB: {e}")
    exit(1)

# ---------------- Data Validation ----------------
if result.empty or len(result) < 48:
    log("[warning] Not enough data to train a reliable model (need at least 2 days). Skipping training.")
    exit()

# ---------------- Data Preparation ----------------
log("Preparing and processing data.")
data = result.rename(columns={"_time": "datetime", "_value": "consumption_kwh"})
data['datetime'] = pd.to_datetime(data['datetime'])
data['hour'] = data['datetime'].dt.hour
data['day_of_week'] = data['datetime'].dt.dayofweek
data['day'] = data['datetime'].dt.day
data['month'] = data['datetime'].dt.month
data['year'] = data['datetime'].dt.year

# ---------------- Feature Engineering ----------------
data['lag_1h'] = data['consumption_kwh'].shift(1)
data['lag_24h'] = data['consumption_kwh'].shift(24)
data = data.dropna()

X = data[['hour', 'day_of_week', 'day', 'month', 'year', 'lag_1h', 'lag_24h']]
y = data['consumption_kwh']
log("Feature engineering completed.")

# ---------------- Model Training ----------------
try:
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    log("Random Forest model trained successfully.")
except Exception as e:
    log(f"[error] Model training failed: {e}")
    exit(1)

# ---------------- Save Model ----------------
try:
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    log(f"Model saved to: {MODEL_PATH}")
except Exception as e:
    log(f"[error] Failed to save model: {e}")
    exit(1)

log("Training script completed successfully.")
