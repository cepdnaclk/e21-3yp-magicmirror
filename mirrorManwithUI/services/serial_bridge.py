import serial
import time
import requests
import re

from config.settings import SERIAL_PORT, SERIAL_BAUD, API_URL

def run_serial_bridge():
    print(f"📡 [Serial Bridge] Connecting to ESP32 via Serial ({SERIAL_PORT} @ {SERIAL_BAUD})...", flush=True)
    ser = None
    last_sent_state = None
    last_sent_time = 0

    while True:
        if ser is None:
            try:
                ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=0.2)
                time.sleep(2)
                print("✅ [Serial Bridge] Connected! Listening for presence/distance signals...", flush=True)
            except Exception as e:
                print(f"⚠️ [Serial Bridge] Serial port ({SERIAL_PORT}) not ready: {e}. Retrying in 5s...", flush=True)
                time.sleep(5)
                continue

        try:
            raw_line = ser.readline().decode('utf-8', errors='ignore').strip()

            if not raw_line:
                continue

            upper_line = raw_line.upper()

            # Determine state from serial line
            detected_state = None
            if "PRESENT" in upper_line:
                detected_state = "present"
            elif "ABSENT" in upper_line:
                detected_state = "absent"
            else:
                numbers = re.findall(r"[-+]?\d*\.\d+|\d+", raw_line)
                if numbers:
                    dist = float(numbers[0])
                    # If distance is in meters (< 10.0), 2.0m threshold. If cm, 200cm threshold.
                    is_present = (dist < 2.0) if dist < 10.0 else (dist < 200.0)
                    detected_state = "present" if is_present else "absent"

            if detected_state:
                now = time.time()
                # Transmit if state changed OR every 1.0 second heartbeat
                if detected_state != last_sent_state or (now - last_sent_time) >= 1.0:
                    if detected_state != last_sent_state:
                        print(f"📡 [Serial Bridge] State Changed -> {detected_state.upper()}", flush=True)
                        last_sent_state = detected_state
                    last_sent_time = now

                    try:
                        requests.get(API_URL + detected_state, timeout=1.0)
                    except Exception:
                        pass

        except Exception as e:
            print(f"⚠️ [Serial Bridge] Read error: {e}", flush=True)
            ser = None
            time.sleep(2)

if __name__ == "__main__":
    run_serial_bridge()
