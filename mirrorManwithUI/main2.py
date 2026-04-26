import sys
import asyncio
import os
import numpy as np
import pyaudio
import speech_recognition as sr
import difflib
import re
import pyttsx3
import boto3
import json
import uvicorn
import webbrowser
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

# ================= WINDOWS FIX =================
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()
# Ensure your Service Account key is pointed to correctly
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_PATH")
gemini_client = genai.Client(
    vertexai=True, 
    project=os.getenv("GEMINI_PROJECT_ID"), 
    location="global"
)
GEMINI_MODEL = "gemini-3-flash-preview"

CUSTOM_PROMPT = (
    "You are Mirror Man, a smart mirror assistant. "
    "You must ALWAYS reply in natural language. "
    "Respond in the language same as the user, if the user speaks in Sinhala respond in Sinhala. "
    "Keep responses short, warm, friendly, and easy to understand."
)

# Audio Settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
HARDWARE_IN_RATE = 16000
HARDWARE_OUT_RATE = 24000
CHUNK = 1024

pya = pyaudio.PyAudio()


# ================= AWS CONFIGURATION =================
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")

s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

# ================= INITIALIZE FASTAPI =================
app = FastAPI()

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# ================= WEBSOCKET MANAGER =================
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

# Shared UI data
notifications = []
priority_schedule = [
    {"time": "10:00 AM", "name": "Project Presentation", "date": "APR 24"},
    {"time": "02:00 PM", "name": "Lab Session", "date": "APR 24"}
]

# ================= AI BOT =================
class SinhalaBot:
    def __init__(self):
        self.should_exit = False
        self.is_active = False
        self.recognizer = sr.Recognizer()


    async def detect_wake_word(self):
        """Listen for hotwords without blocking the FastAPI server"""
        triggers = ["hey mirror", "mirror", "hai mera", "hey me", "mera"]
        while not self.should_exit:
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    print("?? Listening for 'Hey mirror'...")
                    # FIXED: Added to_thread so it doesn't block the AWS S3 watcher!
                    audio = await asyncio.to_thread(
                        self.recognizer.listen, source, timeout=2.0, phrase_time_limit=3.0
                    )
                try:
                    text = await asyncio.to_thread(self.recognizer.recognize_google, audio)
                    text = text.lower()
                    print(f"?? Detected: {text}")
                    if any(trig in text for trig in triggers):
                        print(f"? Wake word detected! Activating mirror...")
                        await manager.broadcast("active")
                        self.is_active = True
                        return
                except sr.UnknownValueError:
                    pass
            except Exception:
                await asyncio.sleep(0.1)

    async def run_session(self):
        """Continuous Conversation Session"""
        print("?? Conversation Active. Say 'Goodbye' or 'Stop' to exit.")
        consecutive_errors = 0
        shutdown_keywords = ["goodbye", "stop", "shut down", "exit", "bye", "?????????"]

        while self.is_active:
            print("\n?? Listening...")
            await manager.broadcast("listening")

            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                    audio_data = await asyncio.to_thread(
                        self.recognizer.listen, source, timeout=7.0, phrase_time_limit=15.0
                    )
            except sr.WaitTimeoutError:
                print("? Listening timed out. Restarting loop...")
                continue
            except Exception as e:
                print(f"? Microphone error: {e}")
                consecutive_errors += 1
                if consecutive_errors >= 2:
                    self.is_active = False
                continue

            try:
                try:
                    user_text = await asyncio.to_thread(
                        self.recognizer.recognize_google, audio_data, language='si-LK'
                    )
                    print(f"?? You said: {user_text}")
                except sr.UnknownValueError:
                    user_text = ""
                except Exception as e:
                    user_text = ""

                if not user_text or not user_text.strip():
                    print("?? No speech detected, ignoring...")
                    continue

                if any(word in user_text.lower() for word in shutdown_keywords):
                    print("?? Shutdown command received.")
                    await asyncio.to_thread(self.speak, "????????, ???? ??????.")
                    self.is_active = False
                    break

                wav_data = audio_data.get_wav_data(convert_rate=16000, convert_width=2)
                print("?? Mirror is thinking...")
                await manager.broadcast("talking")

                response = await asyncio.to_thread(
                gemini_client.models.generate_content,
                model=GEMINI_MODEL,  # Fixed: using the variable defined at the top
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=CUSTOM_PROMPT),
                            types.Part.from_bytes(data=wav_data, mime_type="audio/wav")
                        ]
                    )
                ]
            )

                if response.text:
                    print(f"?? Mirror: {response.text}")
                    await asyncio.to_thread(self.speak, response.text)
                    if "goodbye" in response.text.lower() or "bye" in response.text.lower():
                        self.is_active = False
                    consecutive_errors = 0
                else:
                    consecutive_errors += 1


            except Exception as e:
                print(f"? API Error: {e}")
                consecutive_errors += 1

            if consecutive_errors >= 2:
                self.is_active = False

    def speak(self, text):
        """High-quality Sinhala TTS that preserves your logic flow"""
        try:
            from gtts import gTTS
            import io
            import pygame
            
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            
            tts = gTTS(text=text, lang='si')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            
            pygame.mixer.music.load(fp)
            pygame.mixer.music.play()
            
            # This loop ensures the 'idle' signal doesn't send too early
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
        except Exception as e:
            print(f"? TTS Error: {e}")

    async def run(self):
        while not self.should_exit:
            await self.detect_wake_word()
            if self.is_active:
                # 1. UI changes INSTANTLY
                await manager.broadcast("active") 
                
                # 2. Mirror speaks (logic waits here until audio finishes)
                await asyncio.to_thread(self.speak, "????????! ?? ????? ????, ??? ???????")
                
                # 3. Conversation starts
                await self.run_session()
                
                # 4. Mirror says goodbye (waits for audio to finish)
                print("?? Returning to dashboard...")
                
                # 5. UI returns to normal only AFTER speaking is done
                await manager.broadcast("idle")

bot = SinhalaBot()

# ================= BACKGROUND AWS WATCHER =================
# ================= BACKGROUND AWS WATCHER =================
async def check_s3_inbox():
    """App ????? ??? notifications ?? reminders ??? ???"""
    print("?? Connected to AWS. Watching for App messages...")
    while True:
        try:
            # 1. ?????? (Notifications) ??????? ?????
            notif_res = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix="public/notifications/")
            if 'Contents' in notif_res:
                for item in notif_res['Contents']:
                    file_key = item['Key']
                    if not file_key.endswith('.txt'): continue
                    
                    obj = s3.get_object(Bucket=BUCKET_NAME, Key=file_key)
                    msg = obj['Body'].read().decode('utf-8')
                    
                    print(f"?? APP NOTIFICATION: {msg}")
                    # UI ??? ?????
                    await manager.broadcast(json.dumps({"type": "notification", "message": msg}))
                    # ?????? ?? ????? ?????
                    s3.delete_object(Bucket=BUCKET_NAME, Key=file_key)

            # 2. ???? ?????? (Reminders) ??????? ?????
            rem_res = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix="public/reminders/")
            if 'Contents' in rem_res:
                for item in rem_res['Contents']:
                    file_key = item['Key']
                    if not file_key.endswith('.txt'): continue

                    obj = s3.get_object(Bucket=BUCKET_NAME, Key=file_key)
                    msg = obj['Body'].read().decode('utf-8')
                    
                    print(f"??? NEW REMINDER: {msg}")
                    await manager.broadcast(json.dumps({"type": "reminder", "message": msg}))
                    s3.delete_object(Bucket=BUCKET_NAME, Key=file_key)

        except Exception as e:
            print(f"?? S3 Error: {e}")
            
        await asyncio.sleep(5) # ????? 5?? ?????? ?????

# ================= WEB UI ROUTES =================

@app.get("/api/presence/{status}")
async def presence_trigger(status: str):
   
    # Receives 'present' or 'absent' from the Serial Python script
    # and broadcasts it to the Web UI via WebSockets.
   
    await manager.broadcast(json.dumps({"type": "presence", "value": status}))
    return {"status": "success", "received": status}

@app.get("/")
async def get_html():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    elif os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return HTMLResponse("<h1>index.html not found!</h1>")


@app.get("/api/data")
async def get_sensor_data():
    return {
        "weather": {"temp": 28, "humidity": 80, "description": "Partly Cloudy"},
        "priority_schedule": priority_schedule,
        "notifications": notifications
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    if bot.is_active:
        await websocket.send_text("active")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ================= STARTUP EVENT =================
@app.on_event("startup")
async def startup_event():
    # Start both the Bot and the AWS Watcher alongside the Web Server!
    asyncio.create_task(bot.run())
    asyncio.create_task(check_s3_inbox())

@app.on_event("shutdown")
async def shutdown_event():
    pya.terminate()

# ================= MASTER LAUNCHER =================
if __name__ == "__main__":
    print("?? Starting Mirror Man OS...")
   
    # Define the local URL
    url = "http://127.0.0.1:8000"
   
    # This function opens the browser after a 2-second delay
    # to ensure the server has time to start up.
    def open_browser():
        time.sleep(2)
        print(f"?? Auto-opening dashboard at {url}")
        webbrowser.open(url)

    # We start the browser-opener in a separate thread
    # so it doesn't block the Uvicorn server startup.
    import threading
    import time
    threading.Thread(target=open_browser, daemon=True).start()

    # Use host="127.0.0.1" so the logs show the correct clickable address
    uvicorn.run(app, host="127.0.0.1", port=8000)