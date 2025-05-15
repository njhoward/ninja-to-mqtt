#schedular.py
import threading
import time
import json
import logging
import random
import schedule
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from config import STATUS_LED_ID, EYES_LED_ID, TIME_ZONE
from serialhandler import send_ninjacape_messages
from statehandler import get_state
from persisthandler import get_persisted_state, set_persisted_state
from utils import convert_to_hex, timezone_convert

LEDSLEEP = "LEDSLEEP"

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


def perform_blink(count, blink_color, status_before, eyes_before):

    logging.info(f"[Scheduler] perform_hourly_blink - hour {count}, blink_color {blink_color}, status_before {status_before}, eyes_before {eyes_before}")

    send_led(STATUS_LED_ID, "000000")
    time.sleep(0.2)
    send_led(EYES_LED_ID, "000000")
    time.sleep(2)
    for _ in range(count):
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
    logging.info("[Scheduler] LED colors restored after blinking")


def blink_hourly_leds():
    logging.info(f"[Scheduler] blink_hourly_leds into method")

    if get_persisted_state(LEDSLEEP, "0") == "0":    
        tz_aest = ZoneInfo(TIME_ZONE)
        now_aest = datetime.now(tz_aest)
        blink_hour = now_aest.hour or 12

        logging.info(f"[Scheduler] Blinking {blink_hour} times to mark hour {blink_hour} AEST")

        status_rgb = get_state(str(STATUS_LED_ID), "0,0,255")
        eyes_rgb = get_state(str(EYES_LED_ID), "0,0,255")
        status_before = convert_to_hex(status_rgb) or "0000FF"
        eyes_before = convert_to_hex(eyes_rgb) or "0000FF"
        blink_color = choose_blink_color(status_before, eyes_before)
        logging.info(f"[Scheduler] Blink color chosen: {blink_color}")

        logging.info(f"[Scheduler] blink_hourly_leds - hour {blink_hour}, blink_color {blink_color}, status_before {status_before}, eyes_before {eyes_before}")
        perform_blink(blink_hour, blink_color, status_before, eyes_before)
    else:
        logging.info("[Scheduler] Skipping blink_hourly_leds; LEDSLEEP is active")

def blink_half_hour_beep():
    logging.info("[Scheduler] blink_half_hour_beep into method")

    if get_persisted_state(LEDSLEEP, "0") == "0":
        status_rgb = get_state(str(STATUS_LED_ID), "0,0,255")
        eyes_rgb = get_state(str(EYES_LED_ID), "0,0,255")
        status_before = convert_to_hex(status_rgb) or "0000FF"
        eyes_before = convert_to_hex(eyes_rgb) or "0000FF"
        blink_color = choose_blink_color(status_before, eyes_before)
        
        perform_blink(1, blink_color, status_before, eyes_before)

        logging.info(f"[Scheduler] Half-hour beep color: {blink_color}")
    else:
        logging.info("[Scheduler] Skipping blink_half_hour_beep; LEDSLEEP is active")

def safe_blink_hourly_leds():
    try:
        blink_hourly_leds()
    except Exception as e:
        logging.error(f"[Scheduler] Error in blink_hourly_leds: {e}")
        logging.exception("[Scheduler] Exception details:")

def safe_blink_half_hour_beep():
    try:
        blink_half_hour_beep()
    except Exception as e:
        logging.error(f"[Scheduler] Error in blink_half_hour_beep: {e}")
        logging.exception("[Scheduler] Exception details:")

def turn_leds_off():
    try:
        set_persisted_state(LEDSLEEP, "1")
        status_rgb = get_state(str(STATUS_LED_ID), "0,0,255")
        eyes_rgb = get_state(str(EYES_LED_ID), "0,0,255")
        set_persisted_state(str(STATUS_LED_ID), status_rgb)
        set_persisted_state(str(EYES_LED_ID), eyes_rgb)

        send_led(STATUS_LED_ID, "000000")
        time.sleep(0.2)
        send_led(EYES_LED_ID, "000000")
        logging.info("[Scheduler] LEDs Turned Off")
    except Exception as e:
        logging.error(f"[Scheduler] Error in turn_leds_off: {e}")
        logging.exception("[Scheduler] Exception details:")

def turn_leds_on():
    try:
        set_persisted_state(LEDSLEEP, "0")
        status_rgb = get_persisted_state(str(STATUS_LED_ID), get_state(str(STATUS_LED_ID), "0,0,255"))
        eyes_rgb = get_persisted_state(str(EYES_LED_ID), get_state(str(EYES_LED_ID), "0,0,255"))
        status_before = convert_to_hex(status_rgb) or "0000FF"
        eyes_before = convert_to_hex(eyes_rgb) or "0000FF"
        send_led(STATUS_LED_ID, status_before)
        time.sleep(0.2)
        send_led(EYES_LED_ID, eyes_before)
        logging.info("[Scheduler] LEDs Turned On")
    except Exception as e:
        logging.error(f"[Scheduler] Error in turn_leds_on: {e}")
        logging.exception("[Scheduler] Exception details:")

def run_scheduler():
    try:
        logging.info("[Scheduler] Starting scheduler loop")

        turn_leds_on()

        schedule.every().hour.at(":00").do(safe_blink_hourly_leds)
        schedule.every().hour.at(":30").do(safe_blink_half_hour_beep)

        utc_time = timezone_convert(TIME_ZONE, "UTC", 22, 31)
        utc_str = utc_time.strftime("%H:%M")
        logging.info(f"[Scheduler] Off Set for {utc_str} UTC")
        schedule.every().day.at(utc_str).do(turn_leds_off)

        utc_time = timezone_convert(TIME_ZONE, "UTC", 7, 31)
        utc_str = utc_time.strftime("%H:%M")
        logging.info(f"[Scheduler] On Set for {utc_str} UTC")
        schedule.every().day.at(utc_str).do(turn_leds_on)

        while True:
            try:
                schedule.run_pending()
            except Exception as e:
                logging.error(f"[Scheduler] Error running scheduled tasks: {e}")
                logging.exception("[Scheduler] Exception in scheduler loop")
            time.sleep(1)
    except Exception as e:
        logging.error(f"[Scheduler] Fatal error in run_scheduler: {e}")
        logging.exception("[Scheduler] Exception details at startup or setup")


