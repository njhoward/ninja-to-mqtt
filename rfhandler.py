
def parse_sensor_data(value_str: str) -> dict:
    result = {
        "valid": True,
        "reason": "Parsed successfully",
    }

    try:
        # Support for both decimal and hex
        if value_str.startswith(("0x", "0X")):
            data = int(value_str, 16)
        else:
            data = int(value_str)
    except (ValueError, TypeError):
        return {
            "valid": False,
            "reason": "Invalid input string: not a valid integer"
        }

    # Check 32-bit range
    if not (0 <= data <= 0xFFFFFFFF):
        return {
            "valid": False,
            "reason": "Input out of expected 32-bit unsigned range"
        }

    # Extract fields
    house = (data >> 28) & 0x0F
    station = ((data >> 26) & 0x03) + 1
    humidity = (data >> 16) & 0xFF
    temperature_raw = (data >> 8) & 0xFF
    temperature = temperature_raw - 50

    tempfraction = (data >> 4) & 0x0F
    tempdecimal = ((tempfraction >> 3) & 1) * 0.5 + \
                  ((tempfraction >> 2) & 1) * 0.25 + \
                  ((tempfraction >> 1) & 1) * 0.125 + \
                  (tempfraction & 1) * 0.0625

    temperature = round(temperature + tempdecimal, 1)

    id_field = data & 0x0F
    unknown = (data >> 18) & 0xFF

    # Likelihood checks
    likely_temp = -50 <= temperature <= 60
    likely_humidity = 0 <= humidity <= 100

    if not (likely_temp and likely_humidity):
        result["valid"] = False
        result["reason"] = "Parsed, but values fall outside typical temperature/humidity range"
        result["note"] = "Data may be another device using protocol 5"

    # Always return fields, even if questionable
    result.update({
        "house": house,
        "station": station,
        "humidity": humidity,
        "temperature": temperature,
        "id": id_field,
        "unknown": unknown
    })

    return result
