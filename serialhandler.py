import serial
import json
import logging
from config import SERIAL_PORT, BAUD_RATE, SERIAL_TIMEOUT
from utils import hex_to_rgb_string
from notifier import send_notification

def init_serial():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=SERIAL_TIMEOUT)
        logging.info(f"Serial port {SERIAL_PORT} opened.")
        init_command = json.dumps({"DEVICE": [{"G": "0", "V": 0, "D": 8890, "DA": 1}]})
        ser.write((init_command + "\n").encode("utf-8"))
        logging.info("Sent startup 433MHz enable command.")
        return ser
    except Exception as e:
        logging.error(f"Error opening serial port: {e}")
        exit(1)

def process_ninjacape_messages(ser, mqtt_client):
    while True:
        try:
            raw = ser.readline()
            if not raw:
                continue

            try:
                line = raw.decode("utf-8").strip()
                data = json.loads(line)
            except Exception:
                logging.warning(f"Invalid data received: {raw}")
                send_notification(f"Invalid data: {raw}")
                continue

            if "ACK" in data:
                logging.debug(f"ACK: {data}")
                continue

            if "DEVICE" in data:
                dev = data["DEVICE"][0]
                dev_id = str(dev["D"])
                dev_value = str(dev["DA"])

                #convert to rgb if ninja status (999) or rgb (1007) led's
                if dev_id in {"999", "1007"}:
                    dev_value = hex_to_rgb_string(dev_value)
                
                # Publish received sensor data to MQTT
                mqtt_client.publish(f"ninjaCape/input/{dev_id}", dev_value)

                # log and notify if anything other than 999 or 1007
                if not dev_id in {"999", "1007"}:
                    logging.info(f"Published: {dev_id} -> {dev_value}")
                    send_notification(f"Published: {dev_id} -> {dev_value}")

            else:
                logging.warning(f"Unknown format: {line}")
                send_notification(f"Unknown serial data: {line}")
        except Exception as e:
            logging.error(f"Serial read error: {e}")
            send_notification(f"Serial read error: {e}")
