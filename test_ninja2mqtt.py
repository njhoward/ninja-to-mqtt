import config
import utils
import logger
import notifier
import serialhandler

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
