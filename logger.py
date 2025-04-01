
import logging
import logging.config
import os

# Logging Setup
def setup_logging():
    # Load logging config from external file
    config_file = os.path.join(os.path.dirname(__file__), "logging.conf")
    if os.path.exists(config_file):
        logging.config.fileConfig(config_file)
    else:
        logging.basicConfig(filename='/home/debian/logs/ninja2mqtt.log', level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
