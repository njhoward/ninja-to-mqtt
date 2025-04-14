import logging
import json
import paho.mqtt.client as mqtt
from utils import convert_to_hex
from notifier import send_notification
from config import MQTT_BROKER, MQTT_PORT

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
            logging.debug(f"[MQTTHandler] Serial payload bytes: {(command + '\\n').encode('utf-8')}")

            if int(device_id) == 674:
                logging.info(f"Message from device 674: {moderated}")
                send_notification(f"Message from device 674: {moderated}")


            logging.debug(f"MQTT received on topic: {msg.topic}, payload: {payload}")
            logging.debug(f"Device ID: {device_id}, Moderated: {moderated}")
            logging.debug(f"Final command: {command}")
            logging.debug(f"Bytes sent to serial: {(command + '\\n').encode('utf-8')}")

        except Exception as e:
            logging.error(f"Error processing MQTT message: {e}")
            send_notification(f"MQTT processing error: {e}")

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()
    return client
