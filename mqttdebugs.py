# mqttdebugs.py
import logging
from config import STATUS_LED_ID, EYES_LED_ID
from scheduler import perform_hourly_blink, choose_blink_color
from statehandler import get_all_states, current_states

def handle_debugs(mqttclient, topic, payload):
    if topic == "ninjaCape/debug/states":
        state_snapshot = get_all_states()
        logging.info("Current state dump requested via MQTT:")
        for key, value in state_snapshot.items():
            logging.info(f"  {key}: {value}")
        return f"[Debug] States"  # or return True

    if topic == "ninjaCape/debug/blink":
        try:
            hour = int(payload) if payload.isdigit() else 12
            status_before = current_states.get(str(STATUS_LED_ID), "0000FF")
            eyes_before = current_states.get(str(EYES_LED_ID), "0000FF")
            blink_color = choose_blink_color(status_before, eyes_before)

            perform_hourly_blink(hour, blink_color, status_before, eyes_before)
            logging.info(f"Manually triggered hourly blink for {hour} o'clock")
        except Exception as e:
            logging.error(f"Failed to trigger manual blink: {e}")
        return f"[Debug] Blink triggered for {hour}"  # or return True