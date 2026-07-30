import time
import requests

print("Sending simulated PRESENT signal every 5 seconds...")
while True:
    try:
        requests.get("http://127.0.0.1:8000/api/presence/present")
        time.sleep(5)
    except Exception as e:
        print("Server not running yet...")
        time.sleep(2)
