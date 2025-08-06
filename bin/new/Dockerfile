FROM python:3.11-slim

WORKDIR /app

# Install dependencies using pip only
RUN pip install --no-cache-dir paho-mqtt influxdb-client

# Copy script and make it executable
COPY mqtt_to_db.py /app/mqtt_to_db.py

# Run the script
CMD ["python", "/app/mqtt_to_db.py"]
