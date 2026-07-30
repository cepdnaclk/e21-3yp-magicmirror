import serial
import time
import requests

from config.settings import SERIAL_PORT, SERIAL_BAUD, API_URL

# Configuration
PORT = SERIAL_PORT
BAUD = SERIAL_BAUD

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
            print(">>> Event detected: PRESENT")
            requests.get(API_URL + "present")

        elif "ABSENT" in raw_line:
            print(">>> Event detected: ABSENT")
            requests.get(API_URL + "absent")

    except Exception as e:
        # Ignore minor serial glitches
        pass
