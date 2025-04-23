#schedular.py
import threading
import time
import json
import logging
import random
from datetime import datetime, timedelta
from config import STATUS_LED_ID, EYES_LED_ID
from statehandler import current_states

VALID_LED_COLORS = [
    "FF0000", "00FF00", "0000FF",
    "FFFF00", "00FFFF", "FF00FF", "FFFFFF"
]


def send_led(mqtt_client, device_id, color_hex):
    payload = {
        "DEVICE": [{
            "G": "0",
            "V": 0,
            "D": int(device_id),
            "DA": color_hex
        }]
    }
    topic = f"ninjaCape/output/{device_id}"
    mqtt_client.publish(topic, color_hex)
    logging.info(f"LED {device_id} -> {color_hex}")


def get_next_hour_time(now=None):
    now = now or datetime.now()
    next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    return next_hour


def choose_blink_color(status_color, eyes_color):
    used_colors = {status_color.upper(), eyes_color.upper()}
    available_colors = [c for c in VALID_LED_COLORS if c not in used_colors]
    return random.choice(available_colors or VALID_LED_COLORS)


def perform_hourly_blink(mqtt_client, hour, blink_color, status_before, eyes_before):
    send_led(mqtt_client, STATUS_LED_ID, "000000")
    send_led(mqtt_client, EYES_LED_ID, "000000")
    time.sleep(2)
    for _ in range(hour):
        send_led(mqtt_client, STATUS_LED_ID, blink_color)
        send_led(mqtt_client, EYES_LED_ID, blink_color)
        time.sleep(1)
        send_led(mqtt_client, STATUS_LED_ID, "000000")
        send_led(mqtt_client, EYES_LED_ID, "000000")
        time.sleep(0.5)

    send_led(mqtt_client, STATUS_LED_ID, status_before)
    send_led(mqtt_client, EYES_LED_ID, eyes_before)
    logging.info("LED colors restored after blinking")


def blink_hourly_leds(mqtt_client):
    while True:
        now = datetime.now()
        next_hour = get_next_hour_time(now)
        sleep_time = (next_hour - now).total_seconds()
        logging.info(f"Next blink scheduled in {int(sleep_time)} seconds")
        time.sleep(sleep_time)

        hour = next_hour.hour or 12
        logging.info(f"Blinking {hour} times to mark hour {hour}")

        status_before = current_states.get(str(STATUS_LED_ID), "0000FF")
        eyes_before = current_states.get(str(EYES_LED_ID), "0000FF")
        blink_color = choose_blink_color(status_before, eyes_before)
        logging.info(f"Blink color chosen: {blink_color}")

        perform_hourly_blink(mqtt_client, hour, blink_color, status_before, eyes_before)


def run_scheduler(mqtt_client):
    blink_thread = threading.Thread(target=blink_hourly_leds, args=(mqtt_client,), daemon=True)
    blink_thread.start()
