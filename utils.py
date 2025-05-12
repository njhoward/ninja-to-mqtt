# utils.py
import re
import logging
from zoneinfo import ZoneInfo
from datetime import datetime


def convert_to_hex(value):
    if "," in value:
        try:
            rgb_values = [int(x) for x in value.split(",")]
            return "{:02X}{:02X}{:02X}".format(*rgb_values)
        except ValueError:
            logging.error(f"Invalid RGB tuple received: {value}")
            return None
    return value  # Already hex

def hex_to_tuple(value):
    # Check if value is a valid 6-character hex color
    if re.fullmatch(r'^[0-9A-Fa-f]{6}$', value):
        return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))
    return value  # Return original value if not a valid hex color

def hex_to_rgb_string(hex_color):
    """Convert hex color (e.g., '00FF00') to 'R,G,B' string (e.g., '0,255,0').
       If not a valid hex RGB, return the original value unchanged.
    """
    if re.fullmatch(r'^[0-9A-Fa-f]{6}$', hex_color):
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r},{g},{b}"
    return hex_color  # Return the original value if not valid hex RGB

def is_int(s):
    """Returns True if s is a string that can be converted to an int."""
    try:
        int(s)
        return True
    except (ValueError, TypeError):
        return False

def timezone_convert(timezone_from, timezone_to, hour, minute):
    orig_time = datetime.now(ZoneInfo(timezone_from)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    return orig_time.astimezone(ZoneInfo(timezone_to))

