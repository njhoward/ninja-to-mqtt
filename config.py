import os

# Configuration
SERIAL_PORT = "/dev/ttyS1"
BAUD_RATE = 9600
MQTT_BROKER = "raspberrypi"
MQTT_PORT = 1883
SERIAL_TIMEOUT = 5  # Timeout for serial read to prevent blocking

# PUSHOVER config - retrieved from environment varables
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")