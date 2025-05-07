import shelve
import threading
import os
from config import SHELF_PATH

# Path to persistent shelf file
#SHELF_PATH = '/home/debian/ninja2mqtt_state.db'

# Internal lock for thread safety
_lock = threading.Lock()

def set_persisted_state(key: str, value):
    with _lock:
        with shelve.open(SHELF_PATH, writeback=True) as db:
            db[key] = value

def get_persisted_state(key: str, default=None):
    with _lock:
        with shelve.open(SHELF_PATH) as db:
            return db.get(key, default)

def delete_persisted_state(key: str):
    with _lock:
        with shelve.open(SHELF_PATH, writeback=True) as db:
            if key in db:
                del db[key]

def get_all_persisted_states():
    with _lock:
        with shelve.open(SHELF_PATH) as db:
            return dict(db)  # return as a regular dict for inspection
