# config.py
import os

# Configuration
SERIAL_PORT = "/dev/ttyS1"
BAUD_RATE = 9600
MQTT_BROKER = "raspberrypi"
MQTT_PORT = 1883
SERIAL_TIMEOUT = 5  # Timeout for serial read to prevent blocking

# LED device IDs
STATUS_LED_ID = 999
EYES_LED_ID = 1007

#time zone
TIME_ZONE = "Australia/Melbourne"

#shelving location
SHELF_PATH = '/home/debian/db/ninja2mqtt_state.db'

# PUSHOVER config - retrieved from environment varables
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")

#influx config
INFLUX_HOST = "raspberrypi"
INFLUX_PORT = 8086
INFLUX_DB = "weather_data"
