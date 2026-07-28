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

last_sent_state = None
last_sent_time = 0

while True:
    try:
        # Read the raw line and ignore errors (to handle garbage characters)
        raw_line = ser.readline().decode('utf-8', errors='ignore').strip()

        if not raw_line:
            time.sleep(0.05)
            continue

        print(f"[SERIAL RAW] {raw_line}", flush=True)

        state_detected = None
        if "PRESENT" in raw_line:
            state_detected = "present"
        elif "ABSENT" in raw_line:
            state_detected = "absent"

        if state_detected:
            current_time = time.time()
            # Only trigger HTTP event if the state changed, OR if 10 seconds have passed (keep-alive)
            if state_detected != last_sent_state or (current_time - last_sent_time > 10):
                last_sent_state = state_detected
                last_sent_time = current_time
                print(f">>> Event triggered and sent: {state_detected.upper()}", flush=True)
                threading.Thread(target=send_event, args=(state_detected,), daemon=True).start()

        # Small safeguard delay to prevent CPU hogging
        time.sleep(0.05)

    except Exception as e:
        # Ignore minor serial glitches
        time.sleep(0.1)
