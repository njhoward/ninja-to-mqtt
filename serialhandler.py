# serialhandler.py 
import serial
import json
import logging
from config import SERIAL_PORT, BAUD_RATE, SERIAL_TIMEOUT
from utils import hex_to_rgb_string
from notifier import send_notification
from rfhandler import parse_sensor_data
from rfhandler import log_if_suspicious_rf
from config import STATUS_LED_ID, EYES_LED_ID
from statehandler import set_state
from influxhandler import log_reading
from utils import is_int

ser = None

def init_serial():
    global ser
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=SERIAL_TIMEOUT)
        logging.info(f"Serial port {SERIAL_PORT} opened.")
    except Exception as e:
        logging.error(f"Error opening serial port: {e}")
        exit(1)

def send_ninjacape_messages(command):
    if ser:
        ser.write((command + "\n").encode("utf-8"))
        logging.info(f"Sent to serial: {command}")
    else:
        logging.error("Serial port not initialized.")


def publish_to_mqtt(mqtt_client, topic, payload, dev_id):
    from mqtthandler import publish_payload
    publish_payload(mqtt_client, topic, payload, dev_id=dev_id)


def process_ninjacape_messages(mqtt_client):
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
                if is_int(dev_id) and int(dev_id) in {STATUS_LED_ID, EYES_LED_ID}:
                    dev_value = hex_to_rgb_string(dev_value)

                #logging.debug(f"Dev_ID: {dev_id}, protocol: {protocol}")

                if dev_id == "11": 
                    log_if_suspicious_rf(data, line)
                    if protocol == "5":
                        #logging.debug(f"Dev_ID: 11 and protocol: 5")
                        result = parse_sensor_data(dev_value)
                        if result.get("valid"):

                            # Always log all parsed fields
                            logging.debug(
                                f"Parsed sensor data (raw={dev_value}): "
                                f"House={result.get('house')}, Station={result.get('station')}, "
                                f"Temperature={result.get('temperature')}°C, Humidity={result.get('humidity')}%, "
                                f"ID={result.get('id')}, Unknown={result.get('unknown')} "
                                f"(Valid={result.get('valid')}, Reason={result.get('reason')})"
                            )

                            temp = result["temperature"]
                            hum = result["humidity"]


                            publish_to_mqtt(mqtt_client, "ninjaCape/input/31", temp, dev_id=31)
                            set_state("31", temp)
                            logging.debug(f"[MQTTHandler] Published: (11/5) 31 -> {temp} (temperature)")

                            publish_to_mqtt(mqtt_client, "ninjaCape/input/30", hum, dev_id=30)
                            set_state("30", hum)
                            logging.debug(f"[MQTTHandler] Published: (11/5) 30 -> {hum} (humidity)")

                            #log to influx
                            log_reading("ninja", 3130, result.get('station'), temp, hum)

                            continue  # Skip default publish for dev_id=11 if handled above
                        else:
                            logging.info(f"[MQTTHandler] Unrecognized or non-temperature protocol 5 data: {dev_value} "
                                        f"(Reason: {result.get('reason')})")
                
                # Publish received sensor data to MQTT
                #current_states[dev_id] = dev_value
                set_state(dev_id, dev_value)
                publish_to_mqtt(mqtt_client, f"ninjaCape/input/{dev_id}", dev_value, dev_id=dev_id)


                #Eye and Status LED specific logic
                if is_int(dev_id) and int(dev_id) in {STATUS_LED_ID, EYES_LED_ID}:
                    logging.debug(f"Published dev_id: {dev_id} -> {dev_value}")
                    # specific on / off for LED's
                    on_value = "true"
                    if dev_value == "0,0,0":
                        on_value = "false"
                    publish_to_mqtt(mqtt_client, f"ninjaCape/input/{dev_id}/on", on_value, dev_id=dev_id)
                    logging.debug(f"Published On dev_id: {dev_id} -> {on_value}")
                else:
                    # log and notify if anything other than 999 or 1007
                    logging.info(f"Published Else: {dev_id} -> {dev_value}")
                    send_notification(f"Published Else: {dev_id} -> {dev_value}")

            else:
                logging.warning(f"Unknown format: {line}")
                send_notification(f"Unknown serial data: {line}")
        except Exception as e:
            logging.error(f"Serial read error: {e}")
            send_notification(f"Serial read error: {e}")
