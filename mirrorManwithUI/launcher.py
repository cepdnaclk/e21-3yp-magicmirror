import subprocess
import time
import sys
import os

def start_mirror_system():
    print("🚀 ReflectStudio System Launcher starting...", flush=True)

    # Get the absolute path to the directory containing this script (mirrorManwithUI)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the virtual environment python executable
    if sys.platform.startswith("win"):
        venv_python = os.path.join(base_dir, "..", "venv", "Scripts", "python.exe")
    else:
        venv_python = os.path.join(base_dir, "..", "venv", "bin", "python")
    
    # Use venv_python if it exists, otherwise fallback to sys.executable
    python_exe = venv_python if os.path.exists(venv_python) else sys.executable

    # 1. UI & WebSocket server (app.py)
    ui_proc = subprocess.Popen([python_exe, "app.py"], cwd=base_dir)
    print("✅ Mirror UI & Backend server started.", flush=True)

    # Wait 5 seconds for FastAPI server to be up
    time.sleep(5)

    # 2. Vision Engine
    vision_proc = subprocess.Popen([python_exe, "-m", "services.vision_engine"], cwd=base_dir)
    print("✅ Vision Engine started.", flush=True)

    # 3. Serial Bridge (Presence Sensor)
    serial_proc = subprocess.Popen([python_exe, "-m", "services.serial_bridge"], cwd=base_dir)
    print("✅ Serial Bridge (Presence Sensor) started.", flush=True)

    try:
        ui_proc.wait()
        vision_proc.wait()
        serial_proc.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down all processes...", flush=True)
        ui_proc.terminate()
        vision_proc.terminate()
        serial_proc.terminate()

if __name__ == "__main__":
    start_mirror_system()