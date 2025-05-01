#schedular.py
import threading
import time
import json
import logging
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from config import STATUS_LED_ID, EYES_LED_ID, TIME_ZONE
from serialhandler import send_ninjacape_messages
from statehandler import get_state

VALID_LED_COLORS = [
    "FF0000", "00FF00", "0000FF",
    "FFFF00", "00FFFF", "FF00FF", "FFFFFF"
]


def send_led(device_id, color_hex):
    command = json.dumps({"DEVICE": [{"G": "0", "V": 0, "D": int(device_id), "DA": color_hex}]})
    send_ninjacape_messages(command)
    #topic = f"ninjaCape/output/{device_id}"
    #mqtt_client.publish(topic, color_hex)
    logging.info(f"LED {device_id} -> {color_hex}")


def get_next_hour_time(now=None):
    tz = ZoneInfo(TIME_ZONE)
    now = now or datetime.now(tz)
    next_hour = now.replace(minute=0, second=0, microsecond=0)
    if now >= next_hour:
        next_hour += timedelta(hours=1)
    return next_hour


def choose_blink_color(status_color, eyes_color):
    used_colors = {status_color.upper(), eyes_color.upper()}
    available_colors = [c for c in VALID_LED_COLORS if c not in used_colors]
    return random.choice(available_colors or VALID_LED_COLORS)


def perform_hourly_blink(hour, blink_color, status_before, eyes_before):

    logging.info(f"[Debug] perform_hourly_blink - hour {hour}, blink_color {blink_color}, status_before {status_before}, eyes_before {eyes_before}")

    send_led(STATUS_LED_ID, "000000")
    time.sleep(0.2)
    send_led(EYES_LED_ID, "000000")
    time.sleep(2)
    for _ in range(hour):
        send_led(STATUS_LED_ID, blink_color)
        time.sleep(0.2)
        send_led(EYES_LED_ID, blink_color)
        time.sleep(1)
        send_led(STATUS_LED_ID, "000000")
        time.sleep(0.2)
        send_led(EYES_LED_ID, "000000")
        time.sleep(0.5)

    send_led(STATUS_LED_ID, status_before)
    time.sleep(0.2)
    send_led(EYES_LED_ID, eyes_before)
    logging.info("LED colors restored after blinking")


def blink_hourly_leds():
    logging.info(f"blink_hourly_leds into method")    
    tz_aest = ZoneInfo(TIME_ZONE)
    while True:
        # Use AEST to determine the next AEST hour boundary
        now_aest = datetime.now(tz_aest)
        next_hour_aest = now_aest.replace(minute=0, second=0, microsecond=0)
        if now_aest >= next_hour_aest:
            next_hour_aest += timedelta(hours=1)

        # Convert to UTC for sleep duration
        next_hour_utc = next_hour_aest.astimezone(ZoneInfo("UTC"))
        now_utc = datetime.utcnow()
        sleep_time = (next_hour_utc - now_utc).total_seconds()

        logging.info(f"Next blink scheduled for {next_hour_aest.strftime('%Y-%m-%d %H:%M:%S')} AEST (in {int(sleep_time)} seconds)")
        time.sleep(sleep_time)

        # After waking up, use the AEST hour for blink count
        blink_hour = next_hour_aest.hour or 12
        logging.info(f"Blinking {blink_hour} times to mark hour {blink_hour} AEST")

        status_before = get_state(str(STATUS_LED_ID), "0000FF")
        eyes_before = get_state(str(EYES_LED_ID), "0000FF")
        blink_color = choose_blink_color(status_before, eyes_before)
        logging.info(f"Blink color chosen: {blink_color}")

        perform_hourly_blink(blink_hour, blink_color, status_before, eyes_before)


def run_scheduler():
    blink_thread = threading.Thread(target=blink_hourly_leds, args=(), daemon=True)
    blink_thread.start()
