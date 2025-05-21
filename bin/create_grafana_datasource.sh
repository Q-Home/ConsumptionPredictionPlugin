#!/bin/bash

GRAFANA_CONTAINER="grafana"
INFLUX_URL="http://loxberry:8086"
ORG="Q-Home"
BUCKET="Energy-prediction"
DATASOURCE_NAME="InfluxDB"
TOKEN_FILE="/opt/loxberry/data/plugins/consumption_prediction/.influx_token"
GRAFANA_USER="loxberry"
GRAFANA_PASSWORD="loxberry"

if [ ! -f "$TOKEN_FILE" ]; then
  echo "Token file not found: $TOKEN_FILE"
  exit 1
fi

INFLUX_TOKEN=$(cat "$TOKEN_FILE")

# Create JSON payload for the data source
read -r -d '' DATASOURCE_JSON <<EOF
{
  "name": "$DATASOURCE_NAME",
  "type": "influxdb",
  "access": "proxy",
  "isDefault": true,
  "url": "$INFLUX_URL",
  "jsonData": {
    "version": "Flux",
    "organization": "$ORG",
    "defaultBucket": "$BUCKET"
  },
  "secureJsonData": {
    "token": "$INFLUX_TOKEN"
  }
}
EOF

# Use Grafana's API to create the data source
docker exec "$GRAFANA_CONTAINER" curl -s -X POST http://localhost:3000/api/datasources \
  -H "Content-Type: application/json" \
  -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
  -d "$DATASOURCE_JSON" | grep -q '"datasource"' && \
  echo "Grafana InfluxDB data source created." || \
  echo "Failed to create Grafana data source."