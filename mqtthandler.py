import logging
import json
import time
import paho.mqtt.client as mqtt
from utils import convert_to_hex
from notifier import send_notification
from config import MQTT_BROKER, MQTT_PORT

# Cache of recent publishes
recent_publishes = {}

# Device IDs to throttle
THROTTLED_IDS = {999, 1007, 30, 31}
THROTTLE_SECONDS = 300  # 5 minutes


def setup_mqtt(ser):
    client = mqtt.Client(client_id="beaglebone-ninja")

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info("Connected to MQTT broker")
            client.subscribe("ninjaCape/output/#")
        else:
            logging.error(f"MQTT connection failed with code {rc}")

    def on_message(client, userdata, msg):
        payload = msg.payload.decode()
        device_id = msg.topic.split("/")[-1]
        try:
            #convert to hex if tuple
            moderated = convert_to_hex(payload)
            command = json.dumps({"DEVICE": [{"G": "0", "V": 0, "D": int(device_id), "DA": str(moderated)}]})

             # Send command to NinjaCape via Serial
            ser.write((command + "\n").encode("utf-8"))
            logging.info(f"Sent to serial: {command}")

            if int(device_id) == 674:
                logging.info(f"Message from device 674: {moderated}")
                send_notification(f"Message from device 674: {moderated}")


            #logging.debug(f"MQTT received on topic: {msg.topic}, payload: {payload}")
            #logging.debug(f"Device ID: {device_id}, Moderated: {moderated}")
            #logging.debug(f"Final command: {command}")
            #serial_bytes = (command + "\n").encode("utf-8")
            #logging.debug(f"[MQTTHandler] Serial payload bytes: {serial_bytes}")


        except Exception as e:
            logging.error(f"Error processing MQTT message: {e}")
            send_notification(f"MQTT processing error: {e}")

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()
    return client

def publish_payload(client, topic, payload, dev_id=None):
    """
    Publish to MQTT, applying throttling logic for specific dev_ids.
    """
    if dev_id in THROTTLED_IDS:
        now = time.time()
        last_entry = recent_publishes.get(dev_id)

        if last_entry:
            last_time = last_entry["timestamp"]
            last_value = last_entry["payload"]
            if last_value == payload and now - last_time < THROTTLE_SECONDS:
                logging.debug(f"[MQTTHandler] Throttled publish for device {dev_id} (unchanged, <5m)")
                return  # Do not publish

        # Update cache (because we're publishing)
        recent_publishes[dev_id] = {"timestamp": now, "payload": payload}

    # If not throttled, or conditions allow, publish
    client.publish(topic, payload)
    logging.info(f"Published: {topic} -> {payload}")
