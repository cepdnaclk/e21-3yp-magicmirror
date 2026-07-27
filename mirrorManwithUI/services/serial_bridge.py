import re
import serial
import time
import requests
import sys

from config.settings import (
    SERIAL_PORT, SERIAL_BAUD, API_URL, PRESENCE_MIN_CM, PRESENCE_MAX_CM,
    PRESENCE_DELAY_SECONDS, ABSENCE_DELAY_SECONDS
)

# Configuration
PORT = SERIAL_PORT
BAUD = SERIAL_BAUD

# ── Presence detection thresholds ───────────────────────────────────────────
# These are loaded from config/settings.py (and can be overridden via .env)
# PRESENCE_MIN_CM: readings closer than this are sensor noise (ignored)
# PRESENCE_MAX_CM: readings beyond this = "absent" (default 150 cm)
# PRESENCE_DELAY_SECONDS: time required to trigger "present" (default 5s)
# ABSENCE_DELAY_SECONDS: time required to trigger "absent" (default 15s)
# ────────────────────────────────────────────────────────────────────────────


def connect_serial():
    while True:
        print(f"Connecting to ESP32 via Serial on {PORT}...", flush=True)
        try:
            ser = serial.Serial(PORT, BAUD, timeout=0.1)
            time.sleep(2)
            print("Bridge Active. Parsing distance readings...", flush=True)
            return ser
        except Exception as e:
            print(f"Connection Failed: {e}. Retrying in 5 seconds...", flush=True)
            time.sleep(5)


def parse_distance(line: str):
    """Extract distance in cm from 'Distance: X.XX cm' or return None for NO_ECHO."""
    line_upper = line.upper()

    # Already a PRESENT/ABSENT string from older firmware
    if "PRESENT" in line_upper:
        return "PRESENT"
    if "ABSENT" in line_upper:
        return "ABSENT"

    # NO_ECHO — sensor got no return signal (nothing in range)
    if "NO_ECHO" in line_upper:
        return None  # treat as absent

    # Parse "Distance: 53.25 cm"
    match = re.search(r"Distance:\s*([\d.]+)", line, re.IGNORECASE)
    if match:
        return float(match.group(1))

    return "UNKNOWN"


ser = connect_serial()

current_state = None      # "present" | "absent" | None (unknown)
pending_state = None      # state candidate being debounced
pending_since = None      # timestamp (float) when pending state began
last_logged_second = -1   # throttle candidate log output

while True:
    try:
        raw_line = ser.readline().decode('utf-8', errors='ignore').strip()

        if not raw_line:
            continue

        dist = parse_distance(raw_line)

        # ── Handle legacy PRESENT/ABSENT firmware strings ──
        if dist == "PRESENT":
            new_state = "present"
        elif dist == "ABSENT" or dist is None:
            new_state = "absent"
        elif dist == "UNKNOWN":
            print(f"[Serial Debug] Unrecognised line: '{raw_line}'", flush=True)
            continue
        else:
            # Numeric distance reading
            if PRESENCE_MIN_CM <= dist <= PRESENCE_MAX_CM:
                new_state = "present"
            else:
                new_state = "absent"
            
            # Only print when new state candidate differs from current confirmed state
            if new_state != current_state:
                print(f"[Serial] {dist:.1f} cm → {new_state.upper()}", flush=True)

        # ── Time-based debounce logic ──────────────────────
        if new_state != current_state:
            if new_state != pending_state:
                pending_state = new_state
                pending_since = time.time()
                last_logged_second = -1
                print(f"[Serial] State candidate: {new_state.upper()} (waiting for confirmation...)", flush=True)
            else:
                elapsed = time.time() - pending_since
                required = PRESENCE_DELAY_SECONDS if pending_state == "present" else ABSENCE_DELAY_SECONDS
                if elapsed >= required:
                    current_state = pending_state
                    pending_state = None
                    pending_since = None
                    last_logged_second = -1
                    print(f">>> Presence state changed: {current_state.upper()}", flush=True)
                    requests.get(API_URL + current_state, timeout=2)
                else:
                    # Log state candidate progress once per second
                    elapsed_sec = int(elapsed)
                    if elapsed_sec != last_logged_second:
                        print(f"[Serial] {new_state.upper()} candidate: {elapsed_sec}/{int(required)}s elapsed", flush=True)
                        last_logged_second = elapsed_sec
        else:
            # New reading matches current state, clear pending transitions
            if pending_state is not None:
                print(f"[Serial] Candidate {pending_state.upper()} cleared. Stabilised at: {current_state.upper()}", flush=True)
                pending_state = None
                pending_since = None
                last_logged_second = -1

    except serial.SerialException as se:
        print(f"⚠️ Serial connection lost: {se}. Reconnecting...", flush=True)
        try:
            ser.close()
        except Exception:
            pass
        ser = connect_serial()
        current_state = None
        pending_state = None
        pending_since = None
        last_logged_second = -1
    except Exception as e:
        pass

