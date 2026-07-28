import serial
import time
import requests
import threading

from config.settings import SERIAL_PORT, SERIAL_BAUD, API_URL

# Configuration
PORT = SERIAL_PORT
BAUD = SERIAL_BAUD

def send_event(status):
    try:
        requests.get(API_URL + status, timeout=1.0)
    except Exception:
        pass

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
            time.sleep(0.05)
            continue

        print(f"[SERIAL RAW] {raw_line}", flush=True)

        # Check if the line contains our keywords anywhere within it
        if "PRESENT" in raw_line:
            print(">>> Event detected: PRESENT")
            threading.Thread(target=send_event, args=("present",), daemon=True).start()

        elif "ABSENT" in raw_line:
            print(">>> Event detected: ABSENT")
            threading.Thread(target=send_event, args=("absent",), daemon=True).start()

    except Exception as e:
        # Ignore minor serial glitches
        pass
