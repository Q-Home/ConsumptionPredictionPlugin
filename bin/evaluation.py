#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import joblib
import os
import sys
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient
import subprocess

# ---------------- Configuration ----------------
INFLUX_URL = "http://localhost:8086"
INFLUX_ORG = "Q-Home"
INFLUX_BUCKET = "Energy-prediction"
TOKEN_FILE = "/opt/loxberry/data/plugins/consumption_prediction/.influx_token"
LOGFILE = "/opt/loxberry/data/plugins/consumption_prediction/eval.log"

# Thresholds to trigger retraining (adjust as needed)
MAE_THRESHOLD = 0.3   # kWh
RMSE_THRESHOLD = 0.5  # kWh

# Paths
TRAIN_SCRIPT = "/opt/loxberry/data/plugins/consumption_prediction/train_model.py"

def log(msg):
    os.makedirs(os.path.dirname(LOGFILE), exist_ok=True)
    with open(LOGFILE, "a") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

def read_token():
    try:
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        log(f"[error] Token file not found: {TOKEN_FILE}")
        sys.exit(1)

def get_data(client, query):
    query_api = client.query_api()
    try:
        tables = query_api.query(org=INFLUX_ORG, query=query)
    except Exception as e:
        log(f"[error] InfluxDB query failed: {e}")
        sys.exit(1)
    
    records = []
    for table in tables:
        for record in table.records:
            records.append({
                "datetime": record.get_time(),
                "value": record.get_value()
            })
    return pd.DataFrame(records)

def calculate_metrics(y_true, y_pred):
    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred)**2))
    return mae, rmse

def main():
    log("Starting evaluation script.")

    token = read_token()
    client = InfluxDBClient(url=INFLUX_URL, token=token, org=INFLUX_ORG)

    # Define time range: yesterday 00:00 to 23:00
    yesterday = datetime.now().date() - timedelta(days=1)
    start = datetime.combine(yesterday, datetime.min.time())
    end = start + timedelta(days=1)

    # Query predicted values (assumed measurement: 'predictions' with field 'predicted_kwh')
    query_pred = f'''
    from(bucket: "{INFLUX_BUCKET}")
    |> range(start: "{start.isoformat()}", stop: "{end.isoformat()}")
    |> filter(fn: (r) => r._measurement == "predictions" and r._field == "predicted_kwh")
    |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
    |> yield(name: "mean")
    '''

    df_pred = get_data(client, query_pred)
    if df_pred.empty:
        log("No prediction data found for yesterday. Exiting.")
        return

    df_pred['datetime'] = pd.to_datetime(df_pred['datetime'])
    df_pred = df_pred.set_index('datetime').resample('H').mean().ffill()

    # Query actual consumption values (measurement: 'energy_consumption', field 'consumption_kwh')
    query_actual = f'''
    from(bucket: "{INFLUX_BUCKET}")
    |> range(start: "{start.isoformat()}", stop: "{end.isoformat()}")
    |> filter(fn: (r) => r._measurement == "energy_consumption" and r._field == "consumption_kwh")
    |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
    |> yield(name: "mean")
    '''

    df_actual = get_data(client, query_actual)
    if df_actual.empty:
        log("No actual consumption data found for yesterday. Exiting.")
        return

    df_actual['datetime'] = pd.to_datetime(df_actual['datetime'])
    df_actual = df_actual.set_index('datetime').resample('H').mean().ffill()

    # Align on datetime index
    df = pd.concat([df_actual['value'], df_pred['value']], axis=1)
    df.columns = ['actual_kwh', 'predicted_kwh']
    df.dropna(inplace=True)

    if df.empty:
        log("No overlapping data between actual and predictions. Exiting.")
        return

    mae, rmse = calculate_metrics(df['actual_kwh'], df['predicted_kwh'])
    log(f"Evaluation metrics for {yesterday}: MAE={mae:.3f} kWh, RMSE={rmse:.3f} kWh")

    # Decide if retraining is needed
    if mae > MAE_THRESHOLD or rmse > RMSE_THRESHOLD:
        log(f"Error exceeds threshold (MAE>{MAE_THRESHOLD} or RMSE>{RMSE_THRESHOLD}), retraining model.")
        # Run train_model.py as subprocess
        try:
            subprocess.run(["python3", TRAIN_SCRIPT], check=True)
            log("Model retraining completed successfully.")
        except subprocess.CalledProcessError as e:
            log(f"[error] Retraining failed: {e}")
    else:
        log("Model accuracy within acceptable range. No retraining needed.")

    log("Evaluation script completed.")

if __name__ == "__main__":
    main()
