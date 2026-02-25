import sys
import asyncio
import traceback
import os
import threading
import cv2
import pygame
import numpy as np
import pyaudio
from dotenv import load_dotenv
from google import genai
from google.genai import types

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
# ================= VIDEO PLAYER ======================
# =====================================================

class VideoPlayer:
    def __init__(self, idle_path, talking_path):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 480))
        pygame.display.set_caption("AI Face")

        self.idle_cap = cv2.VideoCapture(idle_path)
        self.talking_cap = cv2.VideoCapture(talking_path)

        self.state = "idle"
        self.running = True
        self.lock = threading.Lock()

    def set_state(self, state):
        with self.lock:
            self.state = state

    def get_frame(self):
        with self.lock:
            cap = self.talking_cap if self.state == "talking" else self.idle_cap

        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()

        frame = cv2.resize(frame, (800, 480))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = np.rot90(frame)
        return pygame.surfarray.make_surface(frame)

    def run(self):
        clock = pygame.time.Clock()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            surface = self.get_frame()
            self.screen.blit(surface, (0, 0))
            pygame.display.update()
            clock.tick(30)

        pygame.quit()

# =====================================================
# =================== AI BOT ==========================
# =====================================================

class SinhalaBot:
    def __init__(self, video_player):
        self.audio_in_queue = None
        self.out_queue = None
        self.session = None
        self.should_exit = False
        self.video_player = video_player
        self.speaking = False

    async def listen_mic(self):
        stream = pya.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=HARDWARE_IN_RATE,
            input=True,
            frames_per_buffer=CHUNK
        )

        while not self.should_exit:
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

        while not self.should_exit:
            data = await self.audio_in_queue.get()

            if not self.speaking:
                self.speaking = True
                self.video_player.set_state("talking")

            await asyncio.to_thread(stream.write, data)

            # Check if queue empty → AI finished speaking
            if self.audio_in_queue.empty():
                self.speaking = False
                self.video_player.set_state("idle")

    async def send_loop(self):
        while not self.should_exit:
            msg = await self.out_queue.get()
            await self.session.send(input=msg)

    async def receive_loop(self):
        while not self.should_exit:
            async for response in self.session.receive():
                if response.data:
                    await self.audio_in_queue.put(response.data)

    async def run(self):
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

# =====================================================
# ================= MAIN ==============================
# =====================================================

if __name__ == "__main__":
    video_player = VideoPlayer("idle.mp4", "talking.mp4")

    video_thread = threading.Thread(target=video_player.run, daemon=True)
    video_thread.start()

    bot = SinhalaBot(video_player)

    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        video_player.running = False
        pya.terminate()
