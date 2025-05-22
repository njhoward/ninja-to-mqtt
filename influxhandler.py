# influxhandler.py

from influxdb import InfluxDBClient
from datetime import datetime
import logging
from config import INFLUX_HOST, INFLUX_PORT, INFLUX_DB

logger = logging.getLogger("influx")

# Initialize InfluxDB client at module level
try:
    influx_client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
    influx_client.switch_database(INFLUX_DB)
    logger.info(f"[Influx] Connected to database '{INFLUX_DB}' at {INFLUX_HOST}:{INFLUX_PORT}")
except Exception as e:
    logger.exception("[Influx] Connection failed during initialization")

def log_reading(model, sensor_id, channel, temperature_C, humidity):
    """Send temperature and humidity data to InfluxDB."""
    if temperature_C is None or humidity is None:
        logger.warning(f"[Influx] Skipped write: missing temperature or humidity: "
                       f"temperature_C={temperature_C}, humidity={humidity}")
        return

    influx_payload = [{
        "measurement": "readings",
        "tags": {
            "model": str(model or "unknown"),
            "sensor_id": str(sensor_id or "unknown"),
            "channel": str(channel or "unknown"),
        },
        "time": datetime.utcnow().isoformat(),
        "fields": {
            "temperature": float(temperature_C),
            "humidity": float(humidity)
        }
    }]

    try:
        influx_client.write_points(influx_payload)
        logger.debug(f"[Influx] Data written: {influx_payload}")
    except Exception as e:
        logger.exception("[Influx] Write operation failed")