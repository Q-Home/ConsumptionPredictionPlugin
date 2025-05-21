
#!/bin/bash

# ----------- Configuration -----------
INFLUX_CONTAINER="influxdb"  # Name of your Docker container
ORG="Q-Home"
BUCKET="Energy-prediction"
TOKEN_FILE="/opt/loxberry/data/plugins/consumption_prediction/.influx_token"
ADMIN_TOKEN="testtoken"

# ----------- Skip if token already exists -----------
if [ -f "$TOKEN_FILE" ]; then
  echo "Token already exists at $TOKEN_FILE"
  exit 0
fi

# ----------- Get Bucket ID -----------
BUCKET_ID=$(docker exec "$INFLUX_CONTAINER" influx bucket list \
  --org "$ORG" \
  --token "$ADMIN_TOKEN" \
  | awk -v bucket="$BUCKET" '$2 == bucket { print $1 }')


if [ -z "$BUCKET_ID" ]; then
  echo "Bucket '$BUCKET' not found. Please check the organization name and bucket name."
  exit 1
fi

# ----------- Create Token -----------
NEW_TOKEN=$(docker exec "$INFLUX_CONTAINER" influx auth create \
  --org "$ORG" \
  --token "$ADMIN_TOKEN" \
  --read-bucket "$BUCKET_ID" \
  --write-bucket "$BUCKET_ID" \
  --description "Auto-token for device MQTT to InfluxDB" \
  --json 2>/dev/null | grep '"token":' | cut -d'"' -f4)

if [ -z "$NEW_TOKEN" ]; then
  echo "Failed to create InfluxDB token."
  exit 1
fi

# ----------- Save Token -----------
mkdir -p "$(dirname "$TOKEN_FILE")"
echo "$NEW_TOKEN" > "$TOKEN_FILE"
chmod 600 "$TOKEN_FILE"

echo "Token created and saved to $TOKEN_FILE"
