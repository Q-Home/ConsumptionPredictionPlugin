#!/bin/bash
DB="/opt/loxberry/data/plugins/consumption_prediction/energy_data.sqlite"

echo "Ensuring SQLite DB schema exists..."

# Create consumption_data table if it doesn't exist
sqlite3 /opt/loxberry/data/plugins/consumption_prediction/energy_data.sqlite "CREATE TABLE IF NOT EXISTS consumption_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    datetime TEXT NOT NULL,
    consumption_kwh REAL NOT NULL
);"

# Create predictions table if it doesn't exist
sqlite3 /opt/loxberry/data/plugins/consumption_prediction/energy_data.sqlite "CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    datetime TEXT NOT NULL,
    predicted_kwh REAL NOT NULL
);"