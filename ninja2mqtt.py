import logging
import threading

from logger import setup_logging
from config import SERIAL_PORT, BAUD_RATE, SERIAL_TIMEOUT
from serialhandler import init_serial, process_ninjacape_messages
from mqtthandler import setup_mqtt
from scheduler import run_scheduler


def main():
    setup_logging()
    logging.info("Starting NinjaCape MQTT Bridge")

    init_serial()
    mqtt_client = setup_mqtt()

    # Start the scheduler after mqtt is ready
    scheduler_thread = threading.Thread(target=run_scheduler, args=(mqtt_client,), daemon=True)
    scheduler_thread.start()

    process_ninjacape_messages(mqtt_client)

if __name__ == "__main__":
    # Main bridge loop
    main()