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
    reading_buffer = []

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

            # 1. Determine raw state for current reading
            current_raw_state = None
            if "PRESENT" in upper_line:
                current_raw_state = "present"
            elif "ABSENT" in upper_line:
                current_raw_state = "absent"
            else:
                numbers = re.findall(r"[-+]?\d*\.\d+|\d+", raw_line)
                if numbers:
                    dist = float(numbers[0])
                    # If distance is in meters (< 10.0), 2.0m threshold. If cm, 200cm threshold.
                    is_present = (dist < 2.0) if dist < 10.0 else (dist < 200.0)
                    current_raw_state = "present" if is_present else "absent"

            if current_raw_state is None:
                continue

            # Maintain moving window of last 3 readings to filter out single-frame sensor noise/spikes
            reading_buffer.append(current_raw_state)
            if len(reading_buffer) > 3:
                reading_buffer.pop(0)

            # Majority vote over buffer
            present_count = reading_buffer.count("present")
            debounced_state = "present" if present_count >= 2 else "absent"

            now = time.time()
            # Send HTTP request if state changed OR heartbeat interval (3s) elapsed
            if debounced_state != last_sent_state or (now - last_sent_time) > 3.0:
                print(f"📡 [Serial Bridge] Event: {debounced_state.upper()}", flush=True)
                try:
                    requests.get(API_URL + debounced_state, timeout=2)
                    last_sent_state = debounced_state
                    last_sent_time = now
                except Exception as req_err:
                    print(f"⚠️ [Serial Bridge] HTTP send error: {req_err}", flush=True)

        except Exception as e:
            print(f"⚠️ [Serial Bridge] Read error: {e}", flush=True)
            ser = None
            time.sleep(2)

if __name__ == "__main__":
    run_serial_bridge()
