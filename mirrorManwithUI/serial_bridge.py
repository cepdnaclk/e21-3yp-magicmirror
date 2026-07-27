import serial
import time
import requests
import threading

# Configuration
PORT = "/dev/ttyUSB0" 
BAUD = 115200
API_URL = "http://127.0.0.1:8000/api/presence/"

# State variables
current_sensor_state = "ABSENT"
current_ui_state = "ABSENT"

presence_timer = None
absence_timer = None
state_lock = threading.Lock()

def send_present():
    global current_ui_state
    with state_lock:
        if current_ui_state != "PRESENT":
            print(">>> UI turned ON (Detected continuous presence for 5 seconds)")
            try:
                requests.get(API_URL + "present")
                current_ui_state = "PRESENT"
            except Exception as e:
                print(f"API Error (present): {e}")

def send_absent():
    global current_ui_state
    with state_lock:
        if current_ui_state != "ABSENT":
            print(">>> UI turned OFF (Continuous absence for 15 seconds)")
            try:
                requests.get(API_URL + "absent")
                current_ui_state = "ABSENT"
            except Exception as e:
                print(f"API Error (absent): {e}")

print("Connecting to ESP32 via Serial...")
try:
    # Adding a timeout to ensure it doesn't get stuck
    ser = serial.Serial(PORT, BAUD, timeout=0.1) 
    time.sleep(2) 
    print("Bridge Active. Listening for PRESENT/ABSENT signals...")
except Exception as e:
    print(f"Connection Failed: {e}")
    exit()

while True:
    try:
        # Read the raw line and ignore errors (to handle garbage characters)
        raw_line = ser.readline().decode('utf-8', errors='ignore').strip()

        if not raw_line:
            continue

        # Check if the line contains our keywords anywhere within it
        if "PRESENT" in raw_line:
            with state_lock:
                if current_sensor_state == "ABSENT":
                    print(">>> Sensor detected: PRESENT (Starting 5s delay timer)")
                    current_sensor_state = "PRESENT"
                    if absence_timer is not None:
                        absence_timer.cancel()
                    presence_timer = threading.Timer(5.0, send_present)
                    presence_timer.start()

        elif "ABSENT" in raw_line:
            with state_lock:
                if current_sensor_state == "PRESENT":
                    print(">>> Sensor detected: ABSENT (Starting 15s delay timer)")
                    current_sensor_state = "ABSENT"
                    if presence_timer is not None:
                        presence_timer.cancel()
                    absence_timer = threading.Timer(15.0, send_absent)
                    absence_timer.start()

    except Exception as e:
        # Ignore minor serial glitches
        pass