import subprocess
import time
import sys
import os

def start_mirror_system():
    print("🪞 ReflectStudio starting...")

    # Get the absolute path to the directory containing this script (mirrorManwithUI)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the virtual environment python executable
    if sys.platform.startswith("win"):
        venv_python = os.path.join(base_dir, "..", "venv", "Scripts", "python.exe")
    else:
        venv_python = os.path.join(base_dir, "..", "venv", "bin", "python")
    
    # Use venv_python if it exists, otherwise fallback to sys.executable
    python_exe = venv_python if os.path.exists(venv_python) else sys.executable
    print(f"🐍 Using Python: {python_exe}", flush=True)

    # --- Helper: start a subprocess with stderr piped for error capture ---
    def start_proc(label, cmd):
        print(f"🚀 Starting {label}: {' '.join(cmd)}", flush=True)
        proc = subprocess.Popen(
            cmd,
            cwd=base_dir,
            stdout=sys.stdout,   # inherit stdout so we see output
            stderr=subprocess.PIPE  # capture stderr to diagnose crashes
        )
        return proc

    def dump_stderr(label, proc):
        """Read and print any stderr output from a crashed process."""
        try:
            stderr_data = proc.stderr.read()
            if stderr_data:
                text = stderr_data.decode('utf-8', errors='replace')
                print(f"\n{'='*60}", flush=True)
                print(f"❌ [{label}] STDERR output (exit code {proc.returncode}):", flush=True)
                print(text, flush=True)
                print(f"{'='*60}\n", flush=True)
        except Exception:
            pass

    # 1. Start UI & WebSocket server (app.py) — this is the CRITICAL process
    ui_proc = start_proc("Mirror UI", [python_exe, "app.py"])
    print("✅ Mirror UI launched.", flush=True)

    # Give the UI server time to initialise before starting other services
    time.sleep(5)

    # 2. Vision Engine
    vision_proc = start_proc("Vision Engine", [python_exe, "-m", "services.vision_engine"])
    print("👁️ Vision Engine started.", flush=True)

    # 3. Serial Bridge (ESP32 Presence Sensor)
    serial_proc = start_proc("Serial Bridge", [python_exe, "-m", "services.serial_bridge"])
    print("🔌 Serial Bridge for ESP32 Presence Sensor started.", flush=True)

    # 4. AI Bot (Isolated Process to prevent PortAudio segfaults from crashing UI)
    bot_proc = start_proc("AI Bot", [python_exe, "-m", "services.bot_runner"])
    print("🤖 AI Bot process started.", flush=True)

    # Build a lookup for logging convenience
    procs = {
        "Mirror UI (app.py)": ui_proc,
        "Vision Engine": vision_proc,
        "Serial Bridge": serial_proc,
        "AI Bot": bot_proc,
    }

    try:
        # Keep running — only exit if the UI process dies
        while True:
            # Check all processes and log any that died
            for label, proc in procs.items():
                rc = proc.poll()
                if rc is not None:
                    print(f"⚠️  [{label}] exited with code {rc}", flush=True)
                    dump_stderr(label, proc)

            # Critical check: if the UI server has crashed, shut everything down
            if ui_proc.poll() is not None:
                print("💀 UI process has died — cannot continue. Shutting down.", flush=True)
                break

            # Remove dead processes from the monitoring dict so we don't spam logs
            procs = {l: p for l, p in procs.items() if p.poll() is None}

            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down ReflectStudio system...")
    finally:
        print("Cleaning up processes...", flush=True)
        for label, proc in [("Mirror UI", ui_proc), ("Vision Engine", vision_proc), ("Serial Bridge", serial_proc), ("AI Bot", bot_proc)]:
            try:
                if proc.poll() is None:
                    proc.terminate()
                    proc.wait(timeout=5)
                    print(f"  ✓ {label} terminated.", flush=True)
                else:
                    print(f"  - {label} already exited (code {proc.returncode}).", flush=True)
            except Exception as e:
                print(f"  ✗ {label} cleanup error: {e}", flush=True)
                try:
                    proc.kill()
                except Exception:
                    pass
        print("🏁 ReflectStudio shutdown complete.", flush=True)

if __name__ == "__main__":
    start_mirror_system()