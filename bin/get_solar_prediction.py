#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import os
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# ---------------- Configuration ----------------
INFLUX_URL = "http://172.20.0.10:8086"
ORG = "Q-Home"
BUCKET = "Energy-prediction"
TOKEN_FILE = "/opt/loxberry/data/plugins/consumption_prediction/.influx_token"
LOGFILE = "/opt/loxberry/data/plugins/consumption_prediction/prediction.log"

# ---------------- Logging ----------------
def log(msg):
    os.makedirs(os.path.dirname(LOGFILE), exist_ok=True)
    with open(LOGFILE, "a") as f:
        timestamp = datetime.now()
        f.write(f"[{timestamp}] [SOLAR] {msg}\n")
        print(f"[{timestamp}] [SOLAR] {msg}")

# ---------------- Load Settings ----------------
file_path = '/opt/loxberry/data/plugins/consumption_prediction/settings.json'
with open(file_path, 'r') as file:
    settings = json.load(file)

LAT = settings['LAT']
LON = settings['LON']
PANEL_AREA = settings['PANEL_AREA']  # in m²
EFFICIENCY = settings['EFFICIENCY']  # efficiency as a decimal (e.g., 0.18 for 18%)

# ---------------- Token Load ----------------
if not os.path.exists(TOKEN_FILE):
    log("ERROR: InfluxDB token file not found.")
    exit(1)

with open(TOKEN_FILE) as f:
    INFLUX_TOKEN = f.read().strip().strip('"')

client_influx = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=ORG
)
write_api = client_influx.write_api(write_options=SYNCHRONOUS)

# ---------------- Influx Write ----------------
def write_to_influx(measurement, field_name, value, timestamp=None):
    timestamp = timestamp or datetime.now()
    point = (
        Point(measurement)
        .field(field_name, value)
        .time(timestamp)
    )
    try:
        write_api.write(bucket=BUCKET, record=point)
        log(f"Wrote to InfluxDB: {measurement} - {field_name}={value:.2f} at {timestamp}")
    except Exception as e:
        log(f"InfluxDB write failed: {e}")

# ---------------- Fetch Forecast from Open-Meteo ----------------
openmeteo_url = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}"
    "&hourly=shortwave_radiation"
    "&timezone=auto"
)

response = requests.get(openmeteo_url)
log(f"Open-Meteo API status: {response.status_code}")

if response.status_code != 200:
    log("Error fetching Open-Meteo forecast.")
    exit(1)

try:
    data = response.json()
except json.JSONDecodeError as e:
    log(f"Failed to decode JSON: {e}")
    log(f"Raw response: {response.text}")
    exit(1)

# ---------------- Process Forecast ----------------
times = data.get("hourly", {}).get("time", [])
radiation_values = data.get("hourly", {}).get("shortwave_radiation", [])

if not times or not radiation_values:
    log("No forecast data received.")
    exit(1)

for i in range(len(times)):
    time_str = times[i]
    radiation = radiation_values[i]

    if radiation is None:
        continue

    try:
        dt = datetime.fromisoformat(time_str)
    except ValueError:
        log(f"Invalid time format: {time_str}")
        continue

    # Convert to kWh: radiation is in W/m²
    kwh = (radiation * PANEL_AREA * EFFICIENCY) / 1000.0

    write_to_influx("solar_forecast", "forecast_kwh", kwh, timestamp=dt)

log("Finished writing Open-Meteo forecast to InfluxDB.")
client_influx.close()
