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
        print(f"Connecting to ESP32 via Serial on {PORT} at {BAUD} baud...", flush=True)
        try:
            ser = serial.Serial(PORT, BAUD, timeout=1)
            # Wait for ESP32 hardware reset + bootloader to complete.
            # The first ~2s of data is ROM bootloader garbage at a different baud rate.
            time.sleep(2)

            # Flush all data that arrived during boot (bootloader junk)
            ser.reset_input_buffer()
            print("Bridge Active. Flushing boot noise... Waiting for Distance readings.", flush=True)

            # Read and discard lines for 1 more second to clear any remaining boot output
            flush_deadline = time.time() + 1.0
            while time.time() < flush_deadline:
                ser.readline()

            print("Bridge ready. Parsing distance readings...", flush=True)

            # Diagnostic: print the first 3 actual lines received so you can verify format
            print("[Serial] Sampling first 3 lines from ESP32:", flush=True)
            for i in range(3):
                sample = ser.readline().decode('utf-8', errors='ignore').strip()
                print(f"  Line {i+1}: '{sample}'", flush=True)

            return ser
        except Exception as e:
            print(f"Connection Failed: {e}. Retrying in 5 seconds...", flush=True)
            time.sleep(5)



def parse_distance(line: str):
    """Extract distance in cm from various firmware formats, or return None for NO_ECHO."""
    line_upper = line.upper()

    # Already a PRESENT/ABSENT string from older firmware
    if "PRESENT" in line_upper:
        return "PRESENT"
    if "ABSENT" in line_upper:
        return "ABSENT"

    # NO_ECHO — sensor got no return signal (nothing in range)
    if "NO_ECHO" in line_upper or "OUT OF RANGE" in line_upper:
        return None  # treat as absent

    # Parse "Distance: 53.25 cm" or "Dist: 53.25" or "D: 53.25cm"
    match = re.search(r"dist(?:ance)?[\s:]+([0-9]+(?:\.[0-9]+)?)", line, re.IGNORECASE)
    if match:
        return float(match.group(1))

    # Bare number with optional "cm" unit — e.g. "53.25" or "53.25 cm"
    match = re.search(r"^([0-9]+(?:\.[0-9]+)?)\s*(?:cm)?$", line.strip(), re.IGNORECASE)
    if match:
        return float(match.group(1))

    # Number followed by "cm" anywhere in line — e.g. "Reading: 53.25cm"
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*cm", line, re.IGNORECASE)
    if match:
        return float(match.group(1))

    return "UNKNOWN"


ser = connect_serial()

current_state = None      # "present" | "absent" | None (unknown)
pending_state = None      # state candidate being debounced
pending_since = None      # timestamp (float) when pending state began
last_logged_second = -1   # throttle candidate log output
last_unrecognized_print_time = 0  # throttle unrecognized line printouts

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
            current_time = time.time()
            if current_time - last_unrecognized_print_time >= 5.0:
                truncated_line = raw_line[:80] + ("..." if len(raw_line) > 80 else "")
                print(f"[Serial Debug] Unrecognised line (throttled): '{truncated_line}'", flush=True)
                last_unrecognized_print_time = current_time
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

