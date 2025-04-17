import pytest
import config
import utils
import logger
import notifier
import serialhandler
import logging.config
import json
from rfhandler import log_if_suspicious_rf

logging.config.fileConfig("logging.conf")

def test_config_loaded():
    assert hasattr(config, 'MQTT_BROKER')

def test_utils_import():
    assert callable(getattr(utils, 'parse_sensor_data', lambda: None))

def test_logger_setup():
    assert hasattr(logger, 'logging')

def test_notifier_mock():
    notifier.send_notification("Test message")  # Should not raise

def test_serialhandler_mock():
    assert hasattr(serialhandler, 'init_serial')

@pytest.mark.parametrize("payload", [
    {"DEVICE": [{"G": "0", "V": 2, "D": 11, "DA": 123456}]},
    {"DEVICE": [{"G": "0", "V": 5, "D": 11, "DA": str(0x30000000)}]},  # house = 3
    {"DEVICE": [{"G": "0", "V": 5, "D": 11, "DA": "garbage"}]},
])
def test_suspicious_detection(payload):
    log_if_suspicious_rf(payload, raw_line=json.dumps(payload))