import serial
import json
import logging
from config import SERIAL_PORT, BAUD_RATE, SERIAL_TIMEOUT
from utils import hex_to_rgb_string
from notifier import send_notification
from rfhandler import parse_sensor_data

def init_serial():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=SERIAL_TIMEOUT)
        logging.info(f"Serial port {SERIAL_PORT} opened.")
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

            # --- Handle ERROR messages ---
            if "ERROR" in data:
                for err in data["ERROR"]:
                    err_msg = err.get("ERR", "Unknown error")
                    err_code = err.get("CODE", "Unknown code")
                    log_msg = f"[SerialHandler] Error received - ERR: {err_msg}, CODE: {err_code}"
                    logging.error(log_msg)

            if "ACK" in data:
                logging.info(f"ACK: {data}")
                continue

            if "DEVICE" in data:
                dev = data["DEVICE"][0]
                protocol = str(dev["V"])
                dev_id = str(dev["D"])
                dev_value = str(dev["DA"])

                #convert to rgb if ninja status (999) or rgb (1007) led's
                if dev_id in {"999", "1007"}:
                    dev_value = hex_to_rgb_string(dev_value)

                if dev_id in "11" and protocol in "5":
                    result = parse_sensor_data(dev_value)
                    if result.get("valid"):
                        logging.debug(f"Received sensor data: Temp={result['temperature']}°C, Humidity={result['humidity']}% "
                                    f"(House={result['house']}, Station={result['station']})")
                        # Example: could publish to MQTT or update internal state
                    else:
                        logging.info(f"Unrecognized or non-temperature protocol 5 data: {dev_value} "
                                    f"(Reason: {result.get('reason')})")
                        # Could choose to skip MQTT, store raw data for review, etc
                
                # Publish received sensor data to MQTT
                mqtt_client.publish(f"ninjaCape/input/{dev_id}", dev_value)

                # log and notify if anything other than 999 or 1007
                if not dev_id in {"999", "1007"}:
                    logging.info(f"Published: {dev_id} -> {dev_value}")
                    send_notification(f"Published: {dev_id} -> {dev_value}")
                else:
                    logging.debug(f"Published: {dev_id} -> {dev_value}")

            else:
                logging.warning(f"Unknown format: {line}")
                send_notification(f"Unknown serial data: {line}")
        except Exception as e:
            logging.error(f"Serial read error: {e}")
            send_notification(f"Serial read error: {e}")
