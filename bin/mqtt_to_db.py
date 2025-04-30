#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import sqlite3
import paho.mqtt.client as mqtt
from datetime import datetime
import signal
import sys

# Configuration
SERVER = "127.0.0.1"
PORT = 1883
TOPIC = "home/energy/consumption"
CLIENT_ID = "python-sqlite-listener"
DB_FILE = "/opt/loxberry/data/plugins/consumption_prediction/energy_data.sqlite"
LOGFILE = "/opt/loxberry/data/plugins/consumption_prediction/mqtt_daemon.log"
MQTT_USERNAME = "loxberry"
MQTT_PASSWORD = "loxberry"
PIDFILE = "/opt/loxberry/data/plugins/consumption_prediction/daemon_script.pid"

# Graceful shutdown
running = True
def signal_handler(sig, frame):
    global running
    running = False
    print("Shutting down...")
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Setup logging
def log(msg):
    with open(LOGFILE, "a") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

# Setup database
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
# Only create the table at start no long-lived connection!
with sqlite3.connect(DB_FILE) as conn:
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS consumption_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        datetime TEXT NOT NULL,
        consumption_kwh REAL NOT NULL
    )
    """)
    conn.commit()

# MQTT callback
def on_message(client, userdata, msg):
    try:
        message = msg.payload.decode()
        consumption = float(message)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Create a new SQLite connection for each message
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO consumption_data (datetime, consumption_kwh) VALUES (?, ?)",
                (now, consumption)
            )
            conn.commit()

        log(f"Got message: {message} | Saved: {consumption} kWh")
    except Exception as e:
        log(f"Error processing message: {e}")

# Start MQTT client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_message = on_message
client.connect(SERVER, PORT, 60)
client.subscribe(TOPIC)
client.loop_start()

# Write PID file
with open(PIDFILE, "w") as f:
    f.write(str(os.getpid()))

log("Daemon script launched")

# Main loop
try:
    while running:
        time.sleep(1)
finally:
    client.loop_stop()
    client.disconnect()
    if os.path.exists(PIDFILE):
        os.remove(PIDFILE)
    log("Daemon script stopped")
