import logging
import json
import time
import paho.mqtt.client as mqtt
from utils import convert_to_hex
from notifier import send_notification
from config import MQTT_BROKER, MQTT_PORT
from statehandler import current_states
from statehandler import get_all_states

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
            client.subscribe("ninjaCape/debug/#")
        else:
            logging.error(f"MQTT connection failed with code {rc}")

    def on_message(client, userdata, msg):
        payload = msg.payload.decode()
        topic = msg.topic
        topic_parts = topic.split("/")
        try:

            if msg.retain:
                logging.debug(
                    f"[MQTTHandler] Skipped retained message from broker — "
                    f"topic: '{msg.topic}', payload: '{msg.payload.decode()}'"
                )
                return

            if topic == "ninjaCape/output":
                logging.debug("Received ninjaCape/output root message — ignoring.")
                return

            if topic == "ninjaCape/debug/states":
                logging.info("states 38")
                state_snapshot = get_all_states()
                logging.info("Current state dump requested via MQTT:")
                for key, value in state_snapshot.items():
                    logging.info(f"  {key}: {value}")
                return
            
            if topic_parts[-1] == "on":
                device_id = int(topic_parts[-2])
                is_on = str(payload).lower() == "true"
                if not is_on:
                    command = json.dumps({"DEVICE": [{"G": "0", "V": 0, "D": int(device_id), "DA": "000000"}]})
                else:
                    return
            else:
                # Handle RGB
                device_id = int(topic_parts[-1])
                #convert to hex if tuple
                moderated = convert_to_hex(payload)
                command = json.dumps({"DEVICE": [{"G": "0", "V": 0, "D": int(device_id), "DA": str(moderated)}]})
                current_states[device_id] = moderated

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

    try:
        dev_id = int(dev_id)
    except (TypeError, ValueError):
        dev_id = None

    if dev_id in THROTTLED_IDS:
        logging.debug(f"[THROTTLE] Checking {dev_id=} {topic=} {payload=}")
        now = time.time()
        cache_key = (dev_id, topic)  # 🔄 Cache key uses dev_id AND topic
        last_entry = recent_publishes.get(cache_key)

        if last_entry:
            last_time = last_entry["timestamp"]
            last_value = last_entry["payload"]
            if last_value == payload and now - last_time < THROTTLE_SECONDS:
                logging.debug(f"[MQTTHandler] Throttled publish for {topic} (dev_id={dev_id}, unchanged, <5m)")
                return

        recent_publishes[cache_key] = {"timestamp": now, "payload": payload}

    client.publish(topic, payload)
    logging.info(f"Published: {topic} -> {payload}")