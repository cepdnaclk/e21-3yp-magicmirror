import serial
import time
import requests
import re

from config.settings import SERIAL_PORT, SERIAL_BAUD, API_URL

def run_serial_bridge():
    print(f"📡 [Serial Bridge] Connecting to ESP32 via Serial ({SERIAL_PORT} @ {SERIAL_BAUD})...", flush=True)
    ser = None

    while True:
        if ser is None:
            try:
                ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=0.5)
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

            # 1. Check explicit string keywords
            if "PRESENT" in upper_line:
                print("📡 [Serial Bridge] Detected: PRESENT", flush=True)
                requests.get(API_URL + "present", timeout=2)
            elif "ABSENT" in upper_line:
                print("📡 [Serial Bridge] Detected: ABSENT", flush=True)
                requests.get(API_URL + "absent", timeout=2)
            else:
                # 2. Support raw distance readings (e.g., "Distance: 150 cm" or "1.8 m")
                numbers = re.findall(r"[-+]?\d*\.\d+|\d+", raw_line)
                if numbers:
                    dist = float(numbers[0])
                    # If distance is in meters (< 10.0), 2.0m threshold. If cm, 200cm threshold.
                    is_present = (dist < 2.0) if dist < 10.0 else (dist < 200.0)
                    status = "present" if is_present else "absent"
                    print(f"📡 [Serial Bridge] Measured Distance ({dist}): {status.upper()}", flush=True)
                    requests.get(API_URL + status, timeout=2)

        except Exception as e:
            print(f"⚠️ [Serial Bridge] Read error: {e}", flush=True)
            ser = None
            time.sleep(2)

if __name__ == "__main__":
    run_serial_bridge()
