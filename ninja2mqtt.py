from logger import setup_logging
from config import SERIAL_PORT, BAUD_RATE, SERIAL_TIMEOUT
from serialhandler import init_serial, process_ninjacape_messages
from mqtthandler import setup_mqtt
import logging

setup_logging()
logging.info("Starting NinjaCape MQTT Bridge")

ser = init_serial()
mqtt_client = setup_mqtt(ser)

process_ninjacape_messages(ser, mqtt_client)
