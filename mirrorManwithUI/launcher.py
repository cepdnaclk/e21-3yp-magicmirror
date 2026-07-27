import subprocess
import time
import sys
import os

def start_mirror_system():
    print("?? ReflectStudio ??????? ??????????...")

    # Get the absolute path to the directory containing this script (mirrorManwithUI)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the virtual environment python executable
    if sys.platform.startswith("win"):
        venv_python = os.path.join(base_dir, "..", "venv", "Scripts", "python.exe")
    else:
        venv_python = os.path.join(base_dir, "..", "venv", "bin", "python")
    
    # Use venv_python if it exists, otherwise fallback to sys.executable
    python_exe = venv_python if os.path.exists(venv_python) else sys.executable

    # 1. UI ?? WebSocket ????????? (app.py) ????? ?????
    ui_proc = subprocess.Popen([python_exe, "app.py"], cwd=base_dir)
    print("? Mirror UI ?? ??????? ????.")

    # UI ?? ??????? ???? ????? 5?? ??????
    time.sleep(5)

    # 2. Vision Engine ?? ????? ?????
    vision_proc = subprocess.Popen([python_exe, "-m", "services.vision_engine"], cwd=base_dir)
    print("👁️ Vision Engine started.")

    # 3. Serial Bridge (ESP32 Presence Sensor)
    serial_proc = subprocess.Popen([python_exe, "-m", "services.serial_bridge"], cwd=base_dir)
    print("🔌 Serial Bridge for ESP32 Presence Sensor started.")

    try:
        # Keep running and monitor processes
        while True:
            if ui_proc.poll() is not None:
                break
            if vision_proc.poll() is not None:
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down ReflectStudio system...")
    finally:
        print("Cleaning up processes...")
        ui_proc.terminate()
        vision_proc.terminate()
        serial_proc.terminate()
        # Wait for shutdown to complete
        ui_proc.wait()
        vision_proc.wait()
        serial_proc.wait()

if __name__ == "__main__":
    start_mirror_system()