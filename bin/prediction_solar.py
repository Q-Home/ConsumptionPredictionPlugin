#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timedelta

# ---------------- Logging Setup ----------------
LOGFILE = "/opt/loxberry/data/plugins/consumption_prediction/prediction.log"

def log(msg):
    os.makedirs(os.path.dirname(LOGFILE), exist_ok=True)
    with open(LOGFILE, "a") as f:
        f.write(f"[{datetime.now()}] [SOLAR] {msg}\n")

log("Starting solar prediction script.")

# ---------------- Config & Settings ----------------
SETTINGS_PATH = "/opt/loxberry/data/plugins/consumption_prediction/settings.json"
TOKEN_FILE = "/opt/loxberry/data/plugins/consumption_prediction/.influx_token"
MODEL_PATH = "/opt/loxberry/data/plugins/consumption_prediction/solar_model.pkl"

try:
    with open(SETTINGS_PATH, "r") as f:
        settings = json.load(f)
    API_KEY = settings.get("openweathermap_api_key")
    print(f"api key: {API_KEY}")
    LAT = settings.get("latitude")
    LON = settings.get("longitude")
    INFLUX_URL = settings.get("influx_url", "http://localhost:8086")
    ORG = settings.get("influx_org", "Q-Home")
    BUCKET = settings.get("influx_bucket", "Energy-prediction")
    if not API_KEY or not LAT or not LON:
        log("[error] Missing API key or location in settings.json")
        exit(1)
    log("Settings loaded successfully.")
except Exception as e:
    log(f"[error] Failed to load settings.json: {e}")
    exit(1)

try:
    with open(TOKEN_FILE, "r") as f:
        INFLUX_TOKEN = f.read().strip()
    log("InfluxDB token loaded successfully.")
except Exception as e:
    log(f"[error] Failed to load InfluxDB token: {e}")
    exit(1)

# ---------------- InfluxDB Client ----------------
try:
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=ORG)
    query_api = client.query_api()
    write_api = client.write_api(write_options=SYNCHRONOUS)
    log("Connected to InfluxDB.")
except Exception as e:
    log(f"[error] Failed to connect to InfluxDB: {e}")
    exit(1)

# ---------------- Fetch Solar Production Data ----------------
query = f'''
from(bucket: "{BUCKET}")
|> range(start: -14d)
|> filter(fn: (r) => r["_measurement"] == "solar_production" and r["_field"] == "production_kwh")
|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
'''

try:
    df = query_api.query_data_frame(org=ORG, query=query)
    if isinstance(df, list) and len(df) > 0:
        df = df[0]
    log("Solar production data queried from InfluxDB.")
except Exception as e:
    log(f"[error] Failed to query solar production data: {e}")
    exit(1)

if df.empty or len(df) < 48:
    log("[warning] Not enough solar production data (need at least 2 days). Exiting.")
    exit(0)

df = df.rename(columns={"_time": "datetime", "production_kwh": "production_kwh"})
df['datetime'] = pd.to_datetime(df['datetime'], utc=True).dt.floor('h')

# ---------------- Fetch Weather Forecast ----------------
def fetch_weather_forecast():
    url = (
        f"https://api.openweathermap.org/data/2.5/forecast?"
        f"lat={LAT}&lon={LON}&appid={API_KEY}&units=metric"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        log("Weather forecast fetched successfully.")
        return data
    except Exception as e:
        log(f"[error] Failed to fetch weather data: {e}")
        return None

forecast_data = fetch_weather_forecast()
if not forecast_data:
    exit(1)

weather_list = forecast_data.get("list", [])
if not weather_list:
    log("[error] No forecast data found in API response.")
    exit(1)

weather_rows = []
for entry in weather_list:
    dt = datetime.utcfromtimestamp(entry["dt"])
    clouds = entry["clouds"]["all"]
    temp = entry["main"]["temp"]
    wind = entry["wind"]["speed"]
    weather_rows.append({"datetime": dt, "clouds": clouds, "temp": temp, "wind": wind})

weather_df = pd.DataFrame(weather_rows)
weather_df['datetime'] = pd.to_datetime(weather_df['datetime'], utc=True).dt.floor('h')

# Interpolate to get hourly data
weather_df = weather_df.set_index('datetime').resample('h').interpolate().reset_index()
print(f"[DEBUG] Weather forecast after interpolation: {len(weather_df)} rows")

# ---------------- Preprocessing ----------------
print(f"[DEBUG] Solar data rows before merge: {len(df)}")
print(f"[DEBUG] Weather forecast rows: {len(weather_df)}")
print(f"[DEBUG] Solar datetime range: {df['datetime'].min()} to {df['datetime'].max()}")
print(f"[DEBUG] Weather datetime range: {weather_df['datetime'].min()} to {weather_df['datetime'].max()}")

# Align data to overlapping period
min_weather_time = weather_df['datetime'].min() - pd.Timedelta('4h')
max_weather_time = weather_df['datetime'].max() + pd.Timedelta('4h')
df = df[(df['datetime'] >= min_weather_time) & (df['datetime'] <= max_weather_time)]

assert df['datetime'].is_unique, "[ERROR] Duplicate datetimes in solar data"
assert weather_df['datetime'].is_unique, "[ERROR] Duplicate datetimes in weather data"


# Merge
merged_df = pd.merge_asof(df.sort_values('datetime'), weather_df.sort_values('datetime'), on='datetime', direction='nearest', tolerance=pd.Timedelta('4h'))
print(f"[DEBUG] Rows after merge: {len(merged_df)}")
print(f"[DEBUG] Rows before dropping NaNs: {len(merged_df)}")

merged_df = merged_df.dropna(subset=['clouds', 'temp', 'wind'])
print(f"[DEBUG] Rows after dropping NaNs: {len(merged_df)}")

# Add time features and lag features
merged_df['hour'] = merged_df['datetime'].dt.hour
merged_df['day_of_week'] = merged_df['datetime'].dt.dayofweek
merged_df['day'] = merged_df['datetime'].dt.day
merged_df['month'] = merged_df['datetime'].dt.month
merged_df['year'] = merged_df['datetime'].dt.year
merged_df = merged_df.sort_values('datetime')
merged_df['lag_1h'] = merged_df['production_kwh'].shift(1)
merged_df['lag_24h'] = merged_df['production_kwh'].shift(24)

print(f"[DEBUG] Rows before dropping NaNs from lag features: {len(merged_df)}")
merged_df = merged_df.dropna(subset=['lag_1h', 'lag_24h'])
print(f"[DEBUG] Rows after dropping NaNs from lag features: {len(merged_df)}")

if merged_df.empty:
    print("[DEBUG] Dataframe is empty after all preprocessing. Exiting.")
    exit(0)

# ---------------- Model Training ----------------
feature_cols = ['hour', 'day_of_week', 'day', 'month', 'year', 'clouds', 'temp', 'wind', 'lag_1h', 'lag_24h']
X_train = merged_df[feature_cols]
y_train = merged_df['production_kwh']

try:
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
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

# ---------------- Predict ----------------
now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
future_times = [now + timedelta(hours=i) for i in range(24)]

weather_pred_rows = []
for t in future_times:
    closest = weather_df.iloc[(weather_df['datetime'] - t).abs().argsort()[:1]].iloc[0]
    weather_pred_rows.append({
        "datetime": t,
        "hour": t.hour,
        "day_of_week": t.weekday(),
        "day": t.day,
        "month": t.month,
        "year": t.year,
        "clouds": closest['clouds'],
        "temp": closest['temp'],
        "wind": closest['wind']
    })

pred_df = pd.DataFrame(weather_pred_rows)
last_known = merged_df.set_index('datetime').sort_index().iloc[-24:]
predictions = []
for i, row in pred_df.iterrows():
    lag_1h = predictions[i-1] if i > 0 else last_known['production_kwh'].iloc[-1]
    lag_24h = last_known['production_kwh'].iloc[-24 + i] if i < 24 else last_known['production_kwh'].iloc[0]
    features = [row[col] for col in ['hour', 'day_of_week', 'day', 'month', 'year', 'clouds', 'temp', 'wind']] + [lag_1h, lag_24h]
    pred = model.predict([features])[0]
    predictions.append(pred)

pred_df['predicted_production_kwh'] = predictions

try:
    for _, r in pred_df.iterrows():
        point = (
            Point("solar_production_prediction")
            .field("predicted_w", float(r['predicted_production_kwh']))
            .time(r['datetime'])
        )
        write_api.write(bucket=BUCKET, record=point)
    log("Predictions for next 24 hours written to InfluxDB.")
except Exception as e:
    log(f"[error] Failed to write predictions to InfluxDB: {e}")
    exit(1)

log("Solar prediction script completed successfully.")
