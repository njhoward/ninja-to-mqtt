import serial
import re
import json
import time
import paho.mqtt.client as mqtt
import logging
import logging.config
import os
import requests

# Configuration
SERIAL_PORT = "/dev/ttyS1"
BAUD_RATE = 9600
MQTT_BROKER = "raspberrypi"
MQTT_PORT = 1883
SERIAL_TIMEOUT = 5  # Timeout for serial read to prevent blocking

# PUSHOVER config - retrieved from environment varables
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")


# Logging Setup
# Load logging config from external file
config_file = os.path.join(os.path.dirname(__file__), "logging.conf")
if os.path.exists(config_file):
    logging.config.fileConfig(config_file)
else:
    logging.basicConfig(filename='/home/debian/logs/ninja2mqtt.log', level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

logging.info("Starting NinjaCape MQTT Bridge")

# Initialize Serial Connection
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=SERIAL_TIMEOUT)
    logging.info(f"Opened serial port {SERIAL_PORT} at {BAUD_RATE} baud")

    init_command = json.dumps({
        "DEVICE": [{
            "G": "0",
            "V": 0,
            "D": 33,
            "DA": int(1)  # Send as an integer, not a string
        }]
    })
    ser.write((init_command + "\n").encode('utf-8'))
    logging.info(f"Sent startup 433MHz enable command: {init_command}")

except Exception as e:
    logging.error(f"Could not open serial port {SERIAL_PORT}: {e}")
    exit(1)

#helper functions

def send_pushover_notification(message):
    """Send a notification to iPhone using Pushover, if credentials are available."""
    if not PUSHOVER_USER_KEY or not PUSHOVER_API_TOKEN:
        logging.error("Pushover environment variables not set. Skipping notification.")
        return

    url = "https://api.pushover.net/1/messages.json"
    payload = {
        "token": PUSHOVER_API_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "message": message,
        "title": "NinjaCape Alert"
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending notification: {e}")

def convert_to_hex(value):
    if "," in value:
        try:
            rgb_values = [int(x) for x in value.split(",")]
            return "{:02X}{:02X}{:02X}".format(*rgb_values)
        except ValueError:
            logging.error(f"Invalid RGB tuple received: {value}")
            return None
    return value  # Already hex

def hex_to_tuple(value):
    # Check if value is a valid 6-character hex color
    if re.fullmatch(r'^[0-9A-Fa-f]{6}$', value):
        return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))
    return value  # Return original value if not a valid hex color

def hex_to_rgb_string(hex_color):
    """Convert hex color (e.g., '00FF00') to 'R,G,B' string (e.g., '0,255,0').
       If not a valid hex RGB, return the original value unchanged.
    """
    if re.fullmatch(r'^[0-9A-Fa-f]{6}$', hex_color):
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r},{g},{b}"
    return hex_color  # Return the original value if not valid hex RGB



# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT Broker")
        client.subscribe("ninjaCape/output/#")
    else:
        logging.error(f"Failed to connect to MQTT, return code {rc}")

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    logging.info(f"Received MQTT message: {msg.topic} -> {payload}")

    # Extract device ID from topic
    try:
        device_id = msg.topic.split("/")[-1]
        
         #convert to hex if tuple
        moderated_send_value = convert_to_hex(payload)
        command = json.dumps({"DEVICE": [{"G": "0", "V": 0, "D": int(device_id), "DA": str(moderated_send_value)}]})

        if int(device_id) == 674:
            send_pushover_notification(f"Message from device 674 received: {str(moderated_send_value)}")
            logging.info(f"Message from device 674 received: {str(moderated_send_value)}")

        # Send command to NinjaCape via Serial
        ser.write((command + "\n").encode('utf-8'))
        logging.info(f"Sent to NinjaCape: {command}")

    except Exception as e:
        logging.error(f"Failed to process MQTT message: {e}")
        send_pushover_notification(f"Failed to process MQTT message: {e}")

# Initialize MQTT Client
mqtt_client = mqtt.Client(client_id="beaglebone-ninja")
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Connect to MQTT Broker
try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
except Exception as e:
    logging.error(f"Cannot connect to MQTT broker: {e}")
    exit(1)

mqtt_client.loop_start()

# Process Serial Data from NinjaCape
def process_ninjacape_messages():
    logging.info("Listening for NinjaCape messages...")
    while True:
        try:
            raw_data = ser.readline()
            if not raw_data:
                continue
            
            try:
                line = raw_data.decode('utf-8').strip()
                logging.debug(f"Received serial data: {line}")
            except UnicodeDecodeError:
                logging.warning(f"Received non-UTF-8 data: {raw_data}")
                send_pushover_notification(f"Received non-UTF-8 data: {raw_data}")
                continue
            
            try:
                data = json.loads(line)


                if "ACK" in data:
                    logging.info(f"Acknowledgment received: {data}")
                    continue  # ACK messages are just acknowledgments, no action needed
              
                if "DEVICE" in data:
                    device = data["DEVICE"][0]
                    dev_id = str(device["D"])
                    dev_value = str(device["DA"])

                    #logging.info(f"prior")
                    if str(dev_id) in {"999", "1007"}:
                        dev_moderated_value = hex_to_rgb_string(dev_value)
                    else:
                        dev_moderated_value = dev_value
                        logging.info(f"Received non-LED serial data: {line}")
                    #logging.info(f"later")

                    # Publish received sensor data to MQTT
                    mqtt_client.publish(f"ninjaCape/input/{dev_id}", str(dev_moderated_value), qos=0, retain=True)

                    if str(dev_id) in {"999", "1007"}:
                        logging.debug(f"Published LED sensor {dev_id} -> {dev_moderated_value}")
                    else:
                        logging.info(f"Published sensor {dev_id} -> {dev_moderated_value}")
                        send_pushover_notification(f"Published sensor {dev_id} -> {dev_moderated_value}")
                else:
                    logging.warning(f"Unknown data format received: {line}")
                    send_pushover_notification(f"Unknown data format received: {line}")

            except json.JSONDecodeError:
                logging.warning(f"Invalid JSON received from serial: {line}")
                send_pushover_notification(f"Invalid JSON received from serial: {line}")
            except KeyError as e:
                logging.warning(f"Missing key {e} in received data: {line}")
                send_pushover_notification(f"Missing key {e} in received data: {line}")

        except Exception as e:
            logging.error(f"Error processing serial data: {e}")
            send_pushover_notification(f"Error processing serial data: {e}")

process_ninjacape_messages()
