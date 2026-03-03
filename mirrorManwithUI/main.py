import sys
import asyncio
import os
import numpy as np
import pyaudio
import speech_recognition as sr
import difflib
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

# ================= WINDOWS FIX =================
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ================= LOAD ENV =================
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MODEL = "models/gemini-2.5-flash-native-audio-preview-12-2025"

CUSTOM_PROMPT = (
    "Your name is PolyglotBot. "
    "Respond in the same language the user speaks."
)

FORMAT = pyaudio.paInt16
CHANNELS = 1
HARDWARE_IN_RATE = 44100
HARDWARE_OUT_RATE = 24000
CHUNK = 1024

client = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=GEMINI_API_KEY
)

CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
)

pya = pyaudio.PyAudio()

# =====================================================
# ================= FASTAPI SERVER ====================
# =====================================================

app = FastAPI()
connected_clients = []

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        connected_clients.remove(websocket)

async def broadcast(message: str):
    for client in connected_clients:
        await client.send_text(message)

# =====================================================
# =================== AI BOT ==========================
# =====================================================

class SinhalaBot:
    def __init__(self):
        self.audio_in_queue = None
        self.out_queue = None
        self.session = None
        self.should_exit = False
        self.speaking = False
        self.is_active = False
        self.recognizer = sr.Recognizer()

    async def detect_wake_word(self):
        """Listen for hotwords including variations like 'Hey Mirror'.

        This accepts exact phrases, substring matches and simple fuzzy
        matches for common mis-recognitions (e.g. 'EMI', 'Mera', 'Hari').
        """
        # canonical triggers and some commonly-observed mis-transcriptions
        triggers = [
            "hey mirror",
            "mirror",
            "play mirror",
            "hey me",
            "mera",
            "meri",
            "emi",
            "emira",
            "yahi mera",
            "hai mera",
            "premi",
            "hari",
            "hari om",
        ]

        # helper for fuzzy word-level matching
        def fuzzy_match_word(word, choices, thresh=0.7):
            for c in choices:
                # ratio on the two tokens
                if difflib.SequenceMatcher(None, word, c).ratio() >= thresh:
                    return c
            return None

        while not self.should_exit:
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    print("🔊 Listening for 'Hey mirror'...")
                    audio = self.recognizer.listen(source, timeout=2.0)

                try:
                    text = self.recognizer.recognize_google(audio)
                    print(f"📝 Detected: {text}")
                    text_lower = text.lower()

                    # direct substring match
                    for trig in triggers:
                        if trig in text_lower:
                            print(f"✅ Wake word detected (matched '{trig}')! Activating mirror...")
                            await broadcast("active")
                            self.is_active = True
                            return

                    # token-level fuzzy matching for short variants
                    tokens = re.findall(r"\w+", text_lower)
                    for t in tokens:
                        match = fuzzy_match_word(t, triggers, thresh=0.75)
                        if match:
                            print(f"✅ Wake word detected (fuzzy '{t}' -> '{match}')! Activating mirror...")
                            await broadcast("active")
                            self.is_active = True
                            return

                except sr.UnknownValueError:
                    pass
                except sr.RequestError:
                    pass
            except sr.RequestError:
                await asyncio.sleep(1)
            except Exception:
                await asyncio.sleep(1)

    async def listen_mic(self):
        stream = pya.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=HARDWARE_IN_RATE,
            input=True,
            frames_per_buffer=CHUNK
        )

        while not self.should_exit and self.is_active:
            data = await asyncio.to_thread(
                stream.read,
                CHUNK,
                exception_on_overflow=False
            )

            audio_array = np.frombuffer(data, dtype=np.int16)
            downsampled = audio_array[::3].tobytes()

            await self.out_queue.put({
                "mime_type": "audio/pcm",
                "data": downsampled
            })

    async def play_speaker(self):
        stream = pya.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=HARDWARE_OUT_RATE,
            output=True
        )

        was_speaking = False
        
        while not self.should_exit and self.is_active:
            if not self.audio_in_queue.empty():
                if not was_speaking:
                    await broadcast("talking")
                    was_speaking = True
                
                data = await self.audio_in_queue.get()
                await asyncio.to_thread(stream.write, data)
            else:
                if was_speaking:
                    await broadcast("listening")
                    was_speaking = False
                await asyncio.sleep(0.1)

    async def send_loop(self):
        while not self.should_exit and self.is_active:
            msg = await self.out_queue.get()
            await self.session.send(input=msg)

    async def receive_loop(self):
        while not self.should_exit and self.is_active:
            async for response in self.session.receive():
                if response.data:
                    await self.audio_in_queue.put(response.data)

    async def run_session(self):
        """Run the AI conversation session"""
        self.audio_in_queue = asyncio.Queue()
        self.out_queue = asyncio.Queue(maxsize=5)

        async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
            self.session = session

            await self.session.send(
                input=CUSTOM_PROMPT,
                end_of_turn=True
            )

            await asyncio.gather(
                self.listen_mic(),
                self.play_speaker(),
                self.receive_loop(),
                self.send_loop()
            )

    async def run(self):
        """Main bot loop - wait for wake word then run session"""
        while not self.should_exit:
            await self.detect_wake_word()
            
            if self.is_active:
                await broadcast("listening")
                await self.run_session()
                self.is_active = False
                await broadcast("idle")

# =====================================================
# ================= MAIN ==============================
# =====================================================

bot = SinhalaBot()

async def main():
    bot_task = asyncio.create_task(bot.run())
    server_task = asyncio.create_task(
        uvicorn.Server(
            uvicorn.Config(app, host="0.0.0.0", port=5000)
        ).serve()
    )
    await asyncio.gather(bot_task, server_task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        pya.terminate()