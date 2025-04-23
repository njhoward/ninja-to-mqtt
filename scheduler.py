# scheduler.py
import schedule
import time
import logging
from notifier import send_notification

def hourly_blink_task():
    now = time.localtime()
    hour = now.tm_hour
    logging.info(f"Blinking {hour} times for hourly schedule")
    send_notification(f"NinjaBlock should blink {hour} times (hourly task)")

def setup_schedule():
    schedule.every().hour.at(":00").do(hourly_blink_task)
    logging.info("Scheduled hourly_blink_task at every hour")

def run_scheduler():
    setup_schedule()
    while True:
        schedule.run_pending()
        time.sleep(1)
