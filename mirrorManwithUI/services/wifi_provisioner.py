import os
import sys
import subprocess
import socket
import time
import threading

# Configuration
HOTSPOT_SSID = "ReflectStudio_Setup"
HOTSPOT_PASSWORD = "reflectstudio123"

# Thread safety lock
wifi_lock = threading.Lock()

def is_connected_to_internet():
    """Checks if the system has an active internet connection by attempting to resolve and connect to a public host."""
    try:
        # Create a connection to a public DNS server
        socket.setdefaulttimeout(3)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except socket.error:
        return False

def start_ap_mode():
    """Starts the local Wi-Fi Hotspot (AP Mode) for provisioning."""
    print(f"📡 [WiFi Provisioner] Starting Hotspot Mode: SSID='{HOTSPOT_SSID}'...")
    
    if sys.platform.startswith("win"):
        # Mock mode on Windows
        print("💡 [WiFi Provisioner] [WINDOWS MOCK] AP Mode active. Clients can connect to mock HTTP endpoints.")
        return True
        
    try:
        # 1. Check if the connection profile already exists
        check_conn = subprocess.run(["nmcli", "connection", "show", HOTSPOT_SSID], capture_output=True)
        
        if check_conn.returncode != 0:
            # 2. Create the hotspot connection profile
            print("📡 [WiFi Provisioner] Creating new nmcli Hotspot profile...")
            subprocess.run([
                "nmcli", "connection", "add", "type", "wifi", "ifname", "wlan0",
                "con-name", HOTSPOT_SSID, "autoconnect", "no", "ssid", HOTSPOT_SSID
            ], check=True)
            
            # 3. Configure the profile as an Access Point (Shared connection)
            subprocess.run([
                "nmcli", "connection", "modify", HOTSPOT_SSID,
                "802-11-wireless.mode", "ap",
                "802-11-wireless-security.key-mgmt", "wpa-psk",
                "802-11-wireless-security.psk", HOTSPOT_PASSWORD,
                "ipv4.method", "shared"
            ], check=True)
            
        # 4. Bring the connection up
        subprocess.run(["nmcli", "connection", "up", HOTSPOT_SSID], check=True)
        print("✅ [WiFi Provisioner] nmcli Hotspot is up and running.")
        return True
    except Exception as e:
        print(f"❌ [WiFi Provisioner] Failed to start Hotspot: {e}")
        return False

def stop_ap_mode():
    """Stops the local Wi-Fi Hotspot."""
    print("📡 [WiFi Provisioner] Stopping Hotspot Mode...")
    
    if sys.platform.startswith("win"):
        print("💡 [WiFi Provisioner] [WINDOWS MOCK] AP Mode stopped.")
        return True
        
    try:
        subprocess.run(["nmcli", "connection", "down", HOTSPOT_SSID], check=True)
        print("✅ [WiFi Provisioner] nmcli Hotspot is down.")
        return True
    except Exception as e:
        print(f"❌ [WiFi Provisioner] Failed to stop Hotspot: {e}")
        return False

def connect_to_wifi(ssid: str, password: str):
    """Attempts to connect the device to the user's home Wi-Fi network."""
    global wifi_lock
    with wifi_lock:
        print(f"📡 [WiFi Provisioner] Attempting to connect to Wi-Fi: '{ssid}'...")
        
        if sys.platform.startswith("win"):
            # Mock mode on Windows: simulate connection time
            time.sleep(3)
            if password == "fail": # simple way to mock failure
                print("❌ [WiFi Provisioner] [WINDOWS MOCK] Connection failed (simulated).")
                return False, "Simulated network timeout error."
            print("✅ [WiFi Provisioner] [WINDOWS MOCK] Connection successful (simulated).")
            return True, "Connected successfully."
            
        try:
            # 1. Stop the AP hotspot if it is currently running
            stop_ap_mode()
            
            # 2. Connect to the new Wi-Fi network using nmcli
            # nmcli device wifi connect SSID password [options]
            # We set a 15-second timeout to check if connection succeeds
            cmd = ["nmcli", "device", "wifi", "connect", ssid, "password", password]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            
            if result.returncode == 0:
                print(f"✅ [WiFi Provisioner] Successfully connected to '{ssid}'.")
                return True, "Connected successfully."
            else:
                # Re-activate AP mode so the user can try again
                print(f"❌ [WiFi Provisioner] Failed to connect: {result.stderr}")
                start_ap_mode()
                return False, result.stderr
        except subprocess.TimeoutExpired:
            print("❌ [WiFi Provisioner] Connection attempt timed out.")
            start_ap_mode()
            return False, "Connection timed out. Please check your SSID or Password."
        except Exception as e:
            print(f"❌ [WiFi Provisioner] Error during connection: {e}")
            start_ap_mode()
            return False, str(e)

async def network_monitor(websocket_manager):
    """Monitors network connection. If offline, activates AP mode and notifies UI."""
    import asyncio
    import json
    
    # Wait a few seconds after boot to let network interfaces settle
    await asyncio.sleep(5)
    
    is_setup_mode_active = False
    
    while True:
        connected = await asyncio.to_thread(is_connected_to_internet)
        
        if not connected:
            if not is_setup_mode_active:
                print("⚠️ [WiFi Provisioner] Offline detected! Switching to AP Mode...")
                # Start AP Mode in a background thread to not block event loop
                await asyncio.to_thread(start_ap_mode)
                is_setup_mode_active = True
                
            # Broadcast setup screen to UI via WebSocket
            payload = json.dumps({
                "type": "setup_mode",
                "status": "offline",
                "ssid": HOTSPOT_SSID,
                "password": HOTSPOT_PASSWORD
            })
            await websocket_manager.broadcast(payload)
            
        else:
            if is_setup_mode_active:
                print("✅ [WiFi Provisioner] Online detected! Stopping AP Mode and returning to normal...")
                await asyncio.to_thread(stop_ap_mode)
                is_setup_mode_active = False
                
                # Broadcast back to normal UI
                payload = json.dumps({
                    "type": "setup_mode",
                    "status": "online"
                })
                await websocket_manager.broadcast(payload)
                
        # Run check every 15 seconds
        await asyncio.sleep(15)

