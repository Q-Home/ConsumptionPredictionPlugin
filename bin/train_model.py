#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from influxdb_client import InfluxDBClient
from datetime import datetime
import os

LOGFILE = "/opt/loxberry/data/plugins/consumption_prediction/train_model.log"

def log(msg):
    os.makedirs(os.path.dirname(LOGFILE), exist_ok=True)
    with open(LOGFILE, "a") as f:
        f.write(f"[{datetime.now()}] {msg}\n")
    print(f"[{datetime.now()}] {msg}")

TOKEN_FILE = "/opt/loxberry/data/plugins/consumption_prediction/.influx_token"
MODEL_PATH = "/opt/loxberry/data/plugins/consumption_prediction/energy_model.pkl"
INFLUX_URL = "http://localhost:8086"
ORG = "Q-Home"
BUCKET = "Energy-prediction"

log("Starting model training script.")

try:
    with open(TOKEN_FILE, "r") as f:
        INFLUX_TOKEN = f.read().strip()
    log("InfluxDB token loaded.")
except FileNotFoundError:
    log(f"[error] Token file not found: {TOKEN_FILE}")
    exit(1)

try:
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=ORG)
    query_api = client.query_api()
    log("Connected to InfluxDB.")
except Exception as e:
    log(f"[error] Failed to connect to InfluxDB: {e}")
    exit(1)

query = f'''
from(bucket: "{BUCKET}")
|> range(start: time(v: 0))
|> filter(fn: (r) => r["_measurement"] == "energy_consumption" and r["_field"] == "consumption_kwh")
|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
'''

try:
    result = query_api.query_data_frame(org=ORG, query=query)
    if isinstance(result, list):
        result = pd.concat(result, ignore_index=True)
    log(f"Data queried. Rows: {len(result)}")
except Exception as e:
    log(f"[error] InfluxDB query failed: {e}")
    exit(1)

if result.empty or len(result) < 72:
    log(f"[warning] Not enough data (got {len(result)} rows).")
    exit()

log("Preparing features...")
data = result.rename(columns={"_time": "datetime", "_value": "consumption_kwh"})
data['datetime'] = pd.to_datetime(data['datetime'])

# Time features
data['hour'] = data['datetime'].dt.hour
data['day_of_week'] = data['datetime'].dt.dayofweek
data['day'] = data['datetime'].dt.day
data['month'] = data['datetime'].dt.month
data['year'] = data['datetime'].dt.year
data['is_weekend'] = data['day_of_week'].isin([5, 6]).astype(int)

# Lag & rolling features
data['lag_1h'] = data['consumption_kwh'].shift(1)
data['lag_2h'] = data['consumption_kwh'].shift(2)
data['lag_3h'] = data['consumption_kwh'].shift(3)
data['lag_24h'] = data['consumption_kwh'].shift(24)
data['rolling_mean_3h'] = data['consumption_kwh'].shift(1).rolling(3).mean()
data['rolling_mean_6h'] = data['consumption_kwh'].shift(1).rolling(6).mean()
data = data.dropna()

X = data[['hour', 'day_of_week', 'day', 'month', 'year', 'is_weekend',
          'lag_1h', 'lag_2h', 'lag_3h', 'lag_24h', 'rolling_mean_3h', 'rolling_mean_6h']]
y = data['consumption_kwh']

try:
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    log("Model trained successfully.")
except Exception as e:
    log(f"[error] Model training failed: {e}")
    exit(1)

try:
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    log(f"Model saved to {MODEL_PATH}")
except Exception as e:
    log(f"[error] Failed to save model: {e}")
    exit(1)

log("Training complete.")
