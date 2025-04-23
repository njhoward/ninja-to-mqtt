# statehandler.py

from threading import Lock

current_states = {}
_lock = Lock()

def set_state(key: str, value):
    with _lock:
        current_states[key] = value

def get_state(key: str):
    with _lock:
        return current_states.get(key)

def get_all_states():
    with _lock:
        return dict(current_states)  # shallow copy
