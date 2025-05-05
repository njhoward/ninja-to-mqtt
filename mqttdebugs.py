# mqttdebugs.py
import logging
import time
from config import STATUS_LED_ID, EYES_LED_ID
from scheduler import perform_blink, choose_blink_color, send_led
from statehandler import get_all_states, current_states

def handle_debugs(mqttclient, topic, payload):
    
    if topic == "ninjaCape/debug/states":
        state_snapshot = get_all_states()
        logging.info("Current state dump requested via MQTT:")
        for key, value in state_snapshot.items():
            logging.info(f"  {key}: {value}")
        return f"[Debug] States"  # or return True

    if topic.startswith("ninjaCape/debug/blink"):
        try:

            if topic == "ninjaCape/debug/blink/1007":
                send_led(1007, "000000")
                time.sleep(1)
                send_led(1007, "0000FF")
                time.sleep(1)
                send_led(1007, "00FF00")
            else:
                count = int(payload) if payload.isdigit() else 12
                status_before = current_states.get(str(STATUS_LED_ID), "0000FF")
                eyes_before = current_states.get(str(EYES_LED_ID), "0000FF")
                blink_color = choose_blink_color(status_before, eyes_before)

                perform_blink(count, blink_color, status_before, eyes_before)
                logging.info(f"Manually triggered blink for {count} o'clock")
        except Exception as e:
            logging.error(f"Failed to trigger manual blink: {e}")
        return f"[Debug] Blink triggered for {count} blinks"  # or return True