import serial, json, time
import paho.mqtt.client as mqtt

# Configuration
SERIAL_PORT    = "/dev/ttyS1"        # Serial interface to NinjaCape (UART1)
BAUD_RATE      = 9600
MQTT_BROKER    = "raspberrypi"      # MQTT broker hostname
MQTT_PORT      = 1883
SERIAL_TIMEOUT  = 5  # Timeout for serial read to prevent blocking

# Define devices to initialize
INITIAL_RGB_VALUES = {
    "999": "0000FF",  # Ninja Status LED
    "1007": "0000FF"   # Ninja Eyes LED
}

# Logging function
def log_message(message):
    print(message, flush=True)

log_message("[INFO] Starting NinjaCape MQTT Bridge")

# Initialize serial connection
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=SERIAL_TIMEOUT)
    log_message(f"[INFO] Opened serial port {SERIAL_PORT} at {BAUD_RATE} baud")
except Exception as e:
    log_message(f"[ERROR] Could not open serial port {SERIAL_PORT}: {e}")
    exit(1)

# Initialize MQTT client
mqtt_client = mqtt.Client(client_id="beaglebone-ninja")
mqtt_client.on_connect = lambda client, userdata, flags, rc: log_message("[INFO] MQTT connected")

try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
except Exception as e:
    log_message(f"[ERROR] Cannot connect to MQTT broker: {e}")
    exit(1)
mqtt_client.loop_start()

# Send initialization messages
def set_initial_colors():
    for attempt in range(2):
        for device_id, color in INITIAL_RGB_VALUES.items():
            message = json.dumps({"DEVICE": [{"G": "0", "V": 0, "D": int(device_id), "DA": color}]})
            ser.write((message + "\n").encode('utf-8'))
            log_message(f"[INFO] Attempt {attempt+1}: Sent {device_id} -> {color}")
        time.sleep(1)  # Delay between attempts

set_initial_colors()

# Process incoming messages
def process_ninjacape_messages():
    log_message("[INFO] Entering main loop to process NinjaCape messages")
    while True:
        try:
            raw_data = ser.readline()
            if not raw_data:
                continue  # Skip if no data

            try:
                line = raw_data.decode('utf-8').strip()
                log_message(f"[DEBUG] Raw serial data received: {line}")
            except UnicodeDecodeError:
                log_message(f"[WARNING] Ignoring non-UTF-8 data from serial: {raw_data}")
                continue
            
            if not line:
                continue

            try:
                data = json.loads(line)
                if "DEVICE" not in data:
                    continue
                
                device = data["DEVICE"][0]
                dev_id = str(device["D"])
                dev_value = str(device["DA"])
                
                mqtt_client.publish(f"ninjaCape/input/{dev_id}", dev_value, qos=0, retain=True)
                log_message(f"[INFO] Updated HomeKit UI: {dev_id} -> {dev_value}")
                
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                log_message(f"[ERROR] JSON processing failed: {e}, received: {line}")
        
        except Exception as e:
            log_message(f"[ERROR] Unexpected error while reading serial: {e}")

# Start processing messages
process_ninjacape_messages()
