#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import sqlite3
import joblib
from sklearn.ensemble import RandomForestRegressor
import os

# Connect to SQLite
conn = sqlite3.connect("/opt/loxberry/data/plugins/consumption_prediction/energy_data.sqlite")
data = pd.read_sql_query('SELECT datetime, consumption_kwh FROM consumption_data', conn, parse_dates=['datetime'])
conn.close()

# Check if enough data exists
if len(data) < 48:
    print("Not enough data to train a reliable model (need at least 2 days). Skipping training.")
    exit()

# Feature engineering
data['hour'] = data['datetime'].dt.hour
data['day_of_week'] = data['datetime'].dt.dayofweek
data['day'] = data['datetime'].dt.day
data['month'] = data['datetime'].dt.month
data['year'] = data['datetime'].dt.year

# Lag features
data['lag_1h'] = data['consumption_kwh'].shift(1)
data['lag_24h'] = data['consumption_kwh'].shift(24)
data = data.dropna()

# Features and target
X = data[['hour', 'day_of_week', 'day', 'month', 'year', 'lag_1h', 'lag_24h']]
y = data['consumption_kwh']

# Train model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

# Save model
os.makedirs("/opt/loxberry/data/plugins/consumption_prediction", exist_ok=True)
joblib.dump(model, "/opt/loxberry/data/plugins/consumption_prediction/energy_model.pkl")
print("Model trained and saved.")
