#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import signal
import sys
import paho.mqtt.client as mqtt
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import json

# ---------------- Setup Logging ----------------
LOGFILE = "/opt/loxberry/data/plugins/consumption_prediction/mqtt_daemon.log"
def log(msg):
    os.makedirs(os.path.dirname(LOGFILE), exist_ok=True)
    with open(LOGFILE, "a") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

# ---------------- Load Settings ----------------
file_path = '/opt/loxberry/data/plugins/consumption_prediction/settings.json'
with open(file_path, 'r') as file:
    settings = json.load(file)

# ---------------- Configuration ----------------
SERVER = settings['mqtt_broker']
PORT = int(settings['mqtt_port'])
TOPIC_CONSUMPTION = settings['mqtt_topic_consumption']
TOPIC_PRODUCTION = settings['mqtt_topic_production']  
TOPIC_LOGS = "home/energy/logs"
MQTT_USERNAME = settings['mqtt_username']
MQTT_PASSWORD = settings['mqtt_password']
print(TOPIC_PRODUCTION)
CLIENT_ID = "python-influx-listener"
TOKEN_FILE = "/opt/loxberry/data/plugins/consumption_prediction/.influx_token"
PIDFILE = "/opt/loxberry/data/plugins/consumption_prediction/daemon_script.pid"
ORG = "Q-Home"
BUCKET = "Energy-prediction"
INFLUX_URL = "http://172.20.0.10:8086"

# ---------------- Read InfluxDB Token ----------------
if not os.path.exists(TOKEN_FILE):
    raise FileNotFoundError(f"Token file not found: {TOKEN_FILE}")

with open(TOKEN_FILE) as f:
    INFLUX_TOKEN = f.read().strip().strip('"')

# ---------------- Graceful Shutdown ----------------
running = True
def signal_handler(sig, frame):
    global running
    running = False
    print("Shutting down...")
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ---------------- InfluxDB Client ----------------
client_influx = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=ORG
)
write_api = client_influx.write_api(write_options=SYNCHRONOUS)

# ---------------- InfluxDB Write Function ----------------
def write_to_influx(measurement, field_name, value, timestamp=None):
    timestamp = timestamp or datetime.now()
    point = (
        Point(measurement)
        .field(field_name, value)
        .time(timestamp)
    )
    try:
        write_api.write(bucket=BUCKET, record=point)
        log(f"Wrote to InfluxDB: {measurement} - {field_name}={value}")
    except Exception as e:
        log(f"InfluxDB write failed: {measurement} - {field_name}={value}. Error: {e}")

# ---------------- MQTT Callback ----------------
def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        message = msg.payload.decode().strip()

        if not message:
            return


        if topic == TOPIC_CONSUMPTION:
            try:
                consumption = float(message)
            except ValueError:
                log(f"Warning: Invalid float on topic '{topic}': '{message}'")
                return
            write_to_influx("energy_consumption", "consumption_kwh", consumption)

        elif topic == TOPIC_PRODUCTION:
            try:
                production = float(message)
                print(f"type of production: {type(production)}")
            except ValueError:
                log(f"Warning: Invalid float on topic '{topic}': '{message}'")
                print(f"Warning: Invalid float on topic '{topic}': '{message}'")
                return
            write_to_influx("solar_production", "production_kwh", production)
            print("wrote" + str(production) + " kWh to productiondb")

        elif topic == TOPIC_LOGS:
            log(f"[MQTT LOG] {message}")

        else:
            log(f"Received message on unknown topic '{topic}': {message}")

    except Exception as e:
        log(f"Error processing message from topic '{msg.topic}': {e}")

# ---------------- Start MQTT ----------------
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_message = on_message
client.connect(SERVER, PORT, 60)
client.subscribe([
    (TOPIC_CONSUMPTION, 0),
    (TOPIC_PRODUCTION, 0),
    (TOPIC_LOGS, 0)
])
client.loop_start()

# ---------------- Write PID ----------------
os.makedirs(os.path.dirname(PIDFILE), exist_ok=True)
with open(PIDFILE, "w") as f:
    f.write(str(os.getpid()))

log("Daemon script launched")

# ---------------- Main Loop ----------------
try:
    while running:
        time.sleep(1)
finally:
    client.loop_stop()
    client.disconnect()
    client_influx.close()
    if os.path.exists(PIDFILE):
        os.remove(PIDFILE)
    log("Daemon script stopped")
