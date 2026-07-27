"""
Standalone mic diagnostic — run directly on the Pi:
  python test_mic.py

This BYPASSES the full system. It:
  1. Lists all audio input devices
  2. Tests opening each one
  3. Attempts speech recognition
"""
import speech_recognition as sr
import sys

print("=" * 60)
print("ReflectStudio Microphone Diagnostic")
print("=" * 60)

r = sr.Recognizer()

# ── 1. List all available devices ──────────────────────────────
print("\n[Step 1] Available microphone devices:")
mics = sr.Microphone.list_microphone_names()
for i, name in enumerate(mics):
    print(f"  [{i}] {name}")

if not mics:
    print("  ERROR: No microphone devices found!")
    sys.exit(1)

# ── 2. Detect which device is the default ──────────────────────
print("\n[Step 2] Default device index:", sr.Microphone().device_index)

# ── 3. Try each device until one captures audio ────────────────
print("\n[Step 3] Testing microphone capture (speak now!)...")
working_index = None

for idx in range(min(len(mics), 6)):  # test first 6 devices
    try:
        with sr.Microphone(device_index=idx) as source:
            print(f"\n  Testing device [{idx}]: {mics[idx]}")
            r.adjust_for_ambient_noise(source, duration=0.5)
            print(f"  → Calibrated. Energy threshold: {r.energy_threshold:.0f}")
            print(f"  → Listening for 3 seconds... SPEAK NOW!")
            audio = r.listen(source, timeout=3.0, phrase_time_limit=4.0)
            print(f"  → Captured {len(audio.frame_data)} bytes of audio")

            # Try recognition
            try:
                text = r.recognize_google(audio, language="en-US")
                print(f"  ✅ Recognised: '{text}'")
                working_index = idx
                break
            except sr.UnknownValueError:
                print(f"  ⚠️  Audio captured but speech not understood (silence or noise?)")
                working_index = idx  # device works, just no recognisable speech
                break
            except sr.RequestError as e:
                print(f"  ⚠️  Google API error: {e}")
                working_index = idx
                break

    except sr.WaitTimeoutError:
        print(f"  ⚠️  No speech detected (timeout) — mic may be wrong or silent")
    except Exception as e:
        print(f"  ❌ Device [{idx}] failed: {e}")

print("\n" + "=" * 60)
if working_index is not None:
    print(f"✅ Working mic device index: {working_index}")
    print(f"   Name: {mics[working_index]}")
    print(f"\n   If this is not index 0, add to services/ai_bot.py:")
    print(f"   sr.Microphone(device_index={working_index})")
else:
    print("❌ No working microphone found. Check USB connection.")
print("=" * 60)
