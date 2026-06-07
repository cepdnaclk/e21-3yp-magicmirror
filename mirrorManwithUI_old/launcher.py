import subprocess
import time
import sys
import webbrowser

def start_mirror_system():
    print("🚀 Starting ReflectStudio System...")
    
    # 1. Start UI and WebSocket Server (main.py)
    ui_proc = subprocess.Popen([sys.executable, "main.py"])
    print("✅ Mirror UI Server activated.")
    
    # Give UI 5 seconds to get ready
    time.sleep(5)
    
    # Auto-open the UI in the default web browser
    print("🌐 Opening Mirror UI in the browser...")
    webbrowser.open("http://127.0.0.1:8000")
    
    # 2. Start Vision Engine
    vision_proc = subprocess.Popen([sys.executable, "vision_engine.py"])
    print("✅ Vision Engine activated.")

    try:
        # Keep system running
        ui_proc.wait()
        vision_proc.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping system...")
        ui_proc.terminate()
        vision_proc.terminate()

if __name__ == "__main__":
    start_mirror_system()