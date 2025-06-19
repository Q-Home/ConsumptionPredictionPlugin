#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from datetime import datetime, timezone, timedelta
import requests
from influxdb_client import InfluxDBClient
import json

# ---------------- Logging Setup ----------------
LOGFILE = "/opt/loxberry/data/plugins/consumption_prediction/loxone_publish.log"

def log(msg):
    os.makedirs(os.path.dirname(LOGFILE), exist_ok=True)
    timestamp = datetime.now()
    with open(LOGFILE, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")
        print(f"[{timestamp}] {msg}\n")

log("Starting Loxone virtual input send script.")

# ---------------- Read InfluxDB Token ----------------
TOKEN_FILE = "/opt/loxberry/data/plugins/consumption_prediction/.influx_token"
if not os.path.exists(TOKEN_FILE):
    raise FileNotFoundError(f"Token file not found: {TOKEN_FILE}")

with open(TOKEN_FILE) as f:
    INFLUX_TOKEN = f.read().strip().strip('"')

# ---------------- Config & Settings ----------------
SETTINGS_PATH = "/opt/loxberry/data/plugins/consumption_prediction/settings.json"

try:
    with open(SETTINGS_PATH, "r") as f:
        settings = json.load(f)
    INFLUX_URL = settings.get("influx_url", "http://localhost:8086")
    ORG = settings.get("influx_org", "Q-Home")
    BUCKET = settings.get("influx_bucket", "Energy-prediction")

    LOXONE_IP = settings.get("loxone_ip", "192.168.1.10")
    LOXONE_USER = settings.get("loxone_user", "Q-Home")
    LOXONE_PASSWORD = settings.get("loxone_password", "qhome2018")

    if not (LOXONE_USER and LOXONE_PASSWORD):
        log("[error] Missing Loxone credentials in settings.json")
        exit(1)

    log("Settings loaded successfully.")
except Exception as e:
    log(f"[error] Failed to load settings.json: {e}")
    exit(1)

# ---------------- InfluxDB Client ----------------
try:
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=ORG)
    query_api = client.query_api()
    log("Connected to InfluxDB.")
except Exception as e:
    log(f"[error] Failed to connect to InfluxDB: {e}")
    exit(1)

# ---------------- Fetch 4-Hour Block Predictions ----------------
def fetch_4hour_block_predictions():
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    end = now + timedelta(hours=24)

    flux_query = f'''
    from(bucket: "{BUCKET}")
    |> range(start: {now.isoformat()}, stop: {end.isoformat()})
    |> filter(fn: (r) => r._measurement == "predictions" and r._field == "predicted_kwh")
    |> keep(columns: ["_time", "_value"])
    '''

    block_totals = {
        "pred_0004": 0.0,
        "pred_0408": 0.0,
        "pred_0812": 0.0,
        "pred_1216": 0.0,
        "pred_1620": 0.0,
        "pred_2024": 0.0
    }

    try:
        tables = query_api.query(flux_query)
        for table in tables:
            for record in table.records:
                ts = record.get_time().astimezone(timezone.utc)
                hour = ts.hour
                value = record.get_value()

                if 0 <= hour < 4:
                    block_totals["pred_0004"] += value
                elif 4 <= hour < 8:
                    block_totals["pred_0408"] += value
                elif 8 <= hour < 12:
                    block_totals["pred_0812"] += value
                elif 12 <= hour < 16:
                    block_totals["pred_1216"] += value
                elif 16 <= hour < 20:
                    block_totals["pred_1620"] += value
                elif 20 <= hour < 24:
                    block_totals["pred_2024"] += value

        log(f"Aggregated consumption predictions: {block_totals}")
        return block_totals

    except Exception as e:
        log(f"[error] Failed to fetch 4-hour predictions: {e}")
        return None

# ---------------- Fetch 4-Hour Block Solar Forecast ----------------
def fetch_4hour_block_solar():
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    end = now + timedelta(hours=24)

    flux_query = f'''
    from(bucket: "{BUCKET}")
    |> range(start: {now.isoformat()}, stop: {end.isoformat()})
    |> filter(fn: (r) => r._measurement == "solar_forecast" and r._field == "predicted_kwh")
    |> keep(columns: ["_time", "_value"])
    '''

    block_totals = {
        "pred_sol_0004": 0.0,
        "pred_sol_0408": 0.0,
        "pred_sol_0812": 0.0,
        "pred_sol_1216": 0.0,
        "pred_sol_1620": 0.0,
        "pred_sol_2024": 0.0
    }

    try:
        tables = query_api.query(flux_query)
        for table in tables:
            for record in table.records:
                ts = record.get_time().astimezone(timezone.utc)
                hour = ts.hour
                value = record.get_value()

                if 0 <= hour < 4:
                    block_totals["pred_sol_0004"] += value
                elif 4 <= hour < 8:
                    block_totals["pred_sol_0408"] += value
                elif 8 <= hour < 12:
                    block_totals["pred_sol_0812"] += value
                elif 12 <= hour < 16:
                    block_totals["pred_sol_1216"] += value
                elif 16 <= hour < 20:
                    block_totals["pred_sol_1620"] += value
                elif 20 <= hour < 24:
                    block_totals["pred_sol_2024"] += value

        log(f"Aggregated solar predictions: {block_totals}")
        return block_totals

    except Exception as e:
        log(f"[error] Failed to fetch solar predictions: {e}")
        return None

# ---------------- Send to Loxone Virtual Inputs ----------------
def send_to_loxone(inputs: dict):
    for virtual_input, value in inputs.items():
        rounded_value = round(value, 3)
        url = f"http://{LOXONE_USER}:{LOXONE_PASSWORD}@{LOXONE_IP}/dev/sps/io/{virtual_input}/{rounded_value}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                log(f"Sent to {virtual_input}: {rounded_value}")
            else:
                log(f"[error] Failed to send to {virtual_input}: {response.status_code} {response.text}")
        except Exception as e:
            log(f"[error] Exception sending to {virtual_input}: {e}")

# ---------------- Main ----------------
predictions = fetch_4hour_block_predictions()
solar_predictions = fetch_4hour_block_solar()

if predictions:
    send_to_loxone(predictions)
else:
    log("No consumption predictions found; nothing sent.")

if solar_predictions:
    send_to_loxone(solar_predictions)
else:
    log("No solar predictions found; nothing sent.")
