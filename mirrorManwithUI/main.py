import sys
import asyncio
import os
import boto3
import json
import uvicorn
import pyaudio
import speech_recognition as sr
import io
import pygame
from gtts import gTTS
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import re
import threading
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import vosk

vosk.SetLogLevel(-1)
vosk_model = vosk.Model("model")

def recognize_vosk_local(audio):
    rec = vosk.KaldiRecognizer(vosk_model, audio.sample_rate)
    rec.SetWords(False)
    rec.AcceptWaveform(audio.get_raw_data())
    res = json.loads(rec.FinalResult())
    return res.get("text", "")

# ================= WINDOWS FIX =================
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ================= CONFIG & PATHS =================
load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

OFFLINE_AUDIO_DIR = os.path.join(BASE_DIR, "offline_audio")
os.makedirs(OFFLINE_AUDIO_DIR, exist_ok=True)

def ensure_offline_audio():
    prompts = {
        "filler.mp3": "Give me a second...",
        "error.mp3": "Sorry, there's a problem with my internet connection.",
        "sleep.mp3": "Okay, I'm going to sleep now.",
        "wakeup.mp3": "Hello! I am ready."
    }
    for filename, text in prompts.items():
        filepath = os.path.join(OFFLINE_AUDIO_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Generating offline audio: {filename}")
            try:
                tts = gTTS(text=text, lang='en')
                tts.save(filepath)
            except Exception as e:
                print(f"Failed to generate {filename}: {e}")

ensure_offline_audio()

# Switched to Gemini API 
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

CUSTOM_PROMPT = (
    "You are Mirror Man, a smart mirror assistant. "
    "You must ALWAYS reply in natural, colloquial English. "
    "Keep responses short, warm, friendly, respectful, and easy to understand."
)

# AWS Config
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
REGION = os.getenv('AWS_DEFAULT_REGION', 'ap-southeast-1')
BUCKET_NAME = os.getenv('BUCKET_NAME')

s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=REGION)
dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=REGION)
REMINDERS_TABLE = os.getenv('DYNAMODB_REMINDERS_TABLE')

# Initialize Pygame for Audio Playback
pygame.mixer.init()

# ================= FASTAPI SETUP =================
app = FastAPI()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

class ConnectionManager:
    def __init__(self):
        self.active_connections = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try: await connection.send_text(message)
            except: pass

manager = ConnectionManager()
seen_notifications = set()
seen_reminders = set()
calendar_events = []

# ================= AI BOT =================
class EnglishBot:
    def __init__(self):
        self.should_exit = False
        self.is_active = False
        self.recognizer = sr.Recognizer()
        self.last_activity_time = None
        self.idle_timeout = 60  # 1 minute timeout
        self.is_talking = False

    def play_offline_audio(self, filename):
        filepath = os.path.join(OFFLINE_AUDIO_DIR, filename)
        if os.path.exists(filepath):
            try:
                pygame.mixer.music.load(filepath)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
            except Exception as e:
                pass

    async def detect_wake_word(self):
        """Listen for hotwords without blocking the FastAPI server"""
        triggers = ["hey mirror", "mirror", "hai mera", "hey me", "mera", "hello mirror", "jamie miller", "amir", "amy", "amira", "am", "play me", "a meta", "the you meet it", "movie mean it", "the me that", "bermuda", "three meta", "hey meta"]
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                while not self.should_exit:
                    try:
                        print("🔊 Listening for 'Hey mirror'...")
                        audio = await asyncio.to_thread(
                            self.recognizer.listen, source, timeout=5.0, phrase_time_limit=3.0
                        )
                        try:
                            text = await asyncio.to_thread(recognize_vosk_local, audio)
                            print(f"📝 Detected Word: {text}")
                            text = text.lower()
                            if any(trig in text for trig in triggers):
                                print(f"✅ Wake word detected! Activating mirror...")
                                self.last_activity_time = asyncio.get_event_loop().time()
                                await manager.broadcast(json.dumps({"type": "mirror_show", "status": "active"}))
                                self.is_active = True
                                self.is_talking = True
                                await manager.broadcast(json.dumps({"type": "status", "state": "listening"}))
                                return
                        except Exception as e:
                            print(f"🔇 (Vosk Error: {e})")
                    except sr.WaitTimeoutError:
                        pass
                    except Exception as e:
                        print(f"⚠️ Microphone error: {e}")
                        await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Microphone Error: {e}")
            await asyncio.sleep(2)

    async def run_session(self):
        """Continuous Conversation Session with timeout"""
        print("🚀 Conversation Active. Say 'Goodbye' or 'Stop' to exit.")
        consecutive_errors = 0
        shutdown_keywords = ["goodbye", "stop", "shut down", "exit", "bye", "sleep", "enough"]

        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                while self.is_active:
                    # Check for 1-minute idle timeout
                    current_time = asyncio.get_event_loop().time()
                    if self.last_activity_time and (current_time - self.last_activity_time) > self.idle_timeout:
                        print("😴 1 minute silence. Putting mirror to sleep...")
                        self.is_talking = False
                        await manager.broadcast(json.dumps({"type": "video", "state": "idle"}))
                        await asyncio.sleep(2)
                        await manager.broadcast(json.dumps({"type": "mirror_hide", "status": "sleep"}))
                        self.is_active = False
                        break

                    print("\n🎤 Listening...")
                    await manager.broadcast(json.dumps({"type": "status", "state": "idle"}))

                    try:
                        audio_data = await asyncio.to_thread(
                            self.recognizer.listen, source, timeout=7.0, phrase_time_limit=15.0
                        )
                    except sr.WaitTimeoutError:
                        print("❌ Listening timed out. Restarting loop...")
                        continue
                    except Exception as e:
                        consecutive_errors += 1
                        if consecutive_errors >= 2: self.is_active = False
                        continue

                    # --- INPUT DETECTION (Sinhala) ---
                    try:
                        try:
                            user_text = await asyncio.to_thread(
                                self.recognizer.recognize_google, audio_data, language='en-US'
                            )
                            print(f"👤 You said: {user_text}")
                        except sr.UnknownValueError:
                            user_text = ""
                        
                        if not user_text or not user_text.strip():
                            continue

                        # Update last activity time on user input
                        self.last_activity_time = asyncio.get_event_loop().time()

                        if any(word in user_text.lower() for word in shutdown_keywords):
                            print("🛑 Shutdown command received.")
                            await manager.broadcast(json.dumps({"type": "video", "state": "talking"}))
                            await asyncio.to_thread(self.play_offline_audio, "sleep.mp3")
                            await manager.broadcast(json.dumps({"type": "mirror_hide", "status": "sleep"}))
                            self.is_active = False
                            break

                        print("☁️ Mirror is thinking...")
                        await manager.broadcast(json.dumps({"type": "status", "state": "thinking"}))
                        
                        self.is_talking = True
                        await manager.broadcast(json.dumps({"type": "video", "state": "talking"}))
                        
                        # Start filler audio (non-blocking)
                        asyncio.create_task(asyncio.to_thread(self.play_offline_audio, "filler.mp3"))

                        # --- GEMINI API CALL (STREAMING & TIMEOUT) ---
                        try:
                            prompt = f"{CUSTOM_PROMPT}\nUser: {user_text}"
                            text_queue = asyncio.Queue()
                            loop = asyncio.get_running_loop()

                            def producer():
                                try:
                                    response = gemini_model.generate_content(prompt, stream=True)
                                    buffer = ""
                                    for chunk in response:
                                        if chunk.text:
                                            buffer += chunk.text
                                            if any(punct in buffer for punct in ['.', '?', '!', ',', '।', '\n']):
                                                parts = re.split(r'([.?!,।\n])', buffer)
                                                sentence = "".join(parts[:-1]).strip()
                                                buffer = parts[-1]
                                                if sentence:
                                                    asyncio.run_coroutine_threadsafe(text_queue.put(sentence), loop)
                                    if buffer.strip():
                                        asyncio.run_coroutine_threadsafe(text_queue.put(buffer.strip()), loop)
                                except Exception as e:
                                    asyncio.run_coroutine_threadsafe(text_queue.put(e), loop)
                                finally:
                                    asyncio.run_coroutine_threadsafe(text_queue.put(None), loop)

                            threading.Thread(target=producer, daemon=True).start()

                            complete_response = ""
                            first_chunk_received = False
                            
                            while True:
                                if not first_chunk_received:
                                    # Wait max 8 seconds for the first chunk to arrive
                                    item = await asyncio.wait_for(text_queue.get(), timeout=8.0)
                                    first_chunk_received = True
                                else:
                                    item = await text_queue.get()
                                
                                if item is None:
                                    break
                                if isinstance(item, Exception):
                                    raise item
                                
                                complete_response += item + " "
                                print(f"🤖 Mirror chunk: {item}")
                                await asyncio.to_thread(self.speak, item)

                            if complete_response:
                                self.last_activity_time = asyncio.get_event_loop().time()
                                if "goodbye" in complete_response.lower() or "bye" in complete_response.lower():
                                    self.is_talking = False
                                    await manager.broadcast(json.dumps({"type": "video", "state": "idle"}))
                                    await asyncio.sleep(2)
                                    await manager.broadcast(json.dumps({"type": "mirror_hide", "status": "sleep"}))
                                    self.is_active = False
                                consecutive_errors = 0
                            else:
                                print("❌ API returned empty response.")
                                consecutive_errors += 1

                        except asyncio.TimeoutError:
                            print("❌ Timeout Error: Internet is too slow.")
                            await asyncio.to_thread(self.play_offline_audio, "error.mp3")
                            consecutive_errors += 1
                        except Exception as api_err:
                            print(f"❌ API Error: {api_err}")
                            await asyncio.to_thread(self.play_offline_audio, "error.mp3")
                            consecutive_errors += 1

                    except Exception as main_err:
                        print(f"❌ Processing Error: {main_err}")
                        consecutive_errors += 1

                    if consecutive_errors >= 2:
                        print("⚠️ Too many errors, returning to sleep.")
                        self.is_talking = False
                        await manager.broadcast(json.dumps({"type": "video", "state": "idle"}))
                        await asyncio.sleep(2)
                        await manager.broadcast(json.dumps({"type": "mirror_hide", "status": "sleep"}))
                        self.is_active = False

        except Exception as session_err:
            print(f"Session Error: {session_err}")
            self.is_active = False

    def speak(self, text):
        """Uses Google Text-To-Speech for English pronunciation"""
        try:
            tts = gTTS(text=text, lang='en') 
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            
            pygame.mixer.music.load(fp)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            print(f"❌ TTS Error: {e}")

    async def run(self):
        """Main loop that manages the UI transition"""
        while not self.should_exit:
            await self.detect_wake_word()
            if self.is_active:
                await manager.broadcast(json.dumps({"type": "mirror_show", "status": "active"}))
                await manager.broadcast(json.dumps({"type": "status", "state": "listening"}))
                await asyncio.sleep(1)
                await manager.broadcast(json.dumps({"type": "video", "state": "talking"}))
                await asyncio.to_thread(self.play_offline_audio, "wakeup.mp3")
                await self.run_session()
                print("💤 Returning to dashboard...")
                await manager.broadcast(json.dumps({"type": "mirror_hide", "status": "sleep"}))

bot = EnglishBot()

# ================= BACKGROUND S3 & DYNAMODB WATCHER =================
async def check_alerts_and_reminders():
    global calendar_events
    while True:
        try:
            # 1. Check alerts in S3
            notif_res = await asyncio.to_thread(s3.list_objects_v2, Bucket=BUCKET_NAME, Prefix="public/notifications/")
            if 'Contents' in notif_res:
                for item in notif_res['Contents']:
                    key = item['Key']
                    if key not in seen_notifications:
                        obj = await asyncio.to_thread(s3.get_object, Bucket=BUCKET_NAME, Key=key)
                        msg = obj['Body'].read().decode('utf-8')
                        print(f"🟢 NOTIFICATION: {msg}")
                        await manager.broadcast(json.dumps({"type": "notification", "message": msg}))
                        seen_notifications.add(key)
                        await asyncio.to_thread(s3.delete_object, Bucket=BUCKET_NAME, Key=key)

            # 2. Check reminders in DynamoDB
            if REMINDERS_TABLE:
                table = dynamodb.Table(REMINDERS_TABLE)
                response = await asyncio.to_thread(table.scan)
                items = response.get('Items', [])
                
                new_events = []
                for item in items:
                    user_id_filter = os.getenv('USER_ID')
                    if user_id_filter and 'owner' in item and user_id_filter not in item['owner']:
                        continue
                    
                    new_events.append({
                        "time": item.get('time', '--:--'),
                        "name": item.get('reason', ''),
                        "date": item.get('date', 'Today')
                    })
                
                for item in items:
                    reminder_id = item.get('id')
                    if reminder_id not in seen_reminders:
                        seen_reminders.add(reminder_id)
                        msg = f"📅 New Task: {item.get('reason')} at {item.get('time')}"
                        await manager.broadcast(json.dumps({"type": "reminder", "message": msg}))

                calendar_events = new_events
        except Exception as e:
            print(f"Error in background watcher: {e}")
        await asyncio.sleep(15)

# ================= ROUTES =================
@app.get("/")
async def get_html():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>index.html not found in static folder!</h1>")

@app.get("/api/data")
async def get_mirror_data():
    return {"weather": {"temp": 28, "humidity": 80, "description": "Clear"}, "priority_schedule": calendar_events}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    if bot.is_active:
        await websocket.send_text("active")
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect: manager.disconnect(websocket)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(bot.run())
    asyncio.create_task(check_alerts_and_reminders())

if __name__ == "__main__":
    print("🚀 Starting Mirror Man OS...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)