import serial
import time
import requests
import sys

from config.settings import SERIAL_PORT, SERIAL_BAUD, API_URL

# Configuration
PORT = SERIAL_PORT
BAUD = SERIAL_BAUD

def connect_serial():
    while True:
        print(f"Connecting to ESP32 via Serial on {PORT}...", flush=True)
        try:
            ser = serial.Serial(PORT, BAUD, timeout=0.1)
            time.sleep(2)
            print("Bridge Active. Listening for PRESENT/ABSENT signals...", flush=True)
            return ser
        except Exception as e:
            print(f"Connection Failed: {e}. Retrying in 5 seconds...", flush=True)
            time.sleep(5)

ser = connect_serial()

while True:
    try:
        # Read the raw line and ignore errors (to handle garbage characters)
        raw_line = ser.readline().decode('utf-8', errors='ignore').strip()

        if not raw_line:
            continue

        # Check if the line contains our keywords anywhere within it (case-insensitive)
        line_upper = raw_line.upper()
        if "PRESENT" in line_upper:
            print(f">>> Event detected: PRESENT (Raw: '{raw_line}')", flush=True)
            requests.get(API_URL + "present", timeout=2)

        elif "ABSENT" in line_upper:
            print(f">>> Event detected: ABSENT (Raw: '{raw_line}')", flush=True)
            requests.get(API_URL + "absent", timeout=2)
            
        else:
            # Print raw line for diagnostics
            print(f"[Serial Debug] Raw line: '{raw_line}'", flush=True)

    except serial.SerialException as se:
        print(f"⚠️ Serial connection lost: {se}. Reconnecting...", flush=True)
        try:
            ser.close()
        except Exception:
            pass
        ser = connect_serial()
    except Exception as e:
        # Ignore other minor glitches
        pass

