import logging
import requests
from config import PUSHOVER_USER_KEY, PUSHOVER_API_TOKEN

def send_notification(message, title="NinjaCape Alert"):
    if not PUSHOVER_USER_KEY or not PUSHOVER_API_TOKEN:
        logging.error("Pushover credentials not set. Skipping notification.")
        return

    try:
        response = requests.post("https://api.pushover.net/1/messages.json", data={
            "token": PUSHOVER_API_TOKEN,
            "user": PUSHOVER_USER_KEY,
            "message": message,
            "title": title
        })
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to send Pushover notification: {e}")
