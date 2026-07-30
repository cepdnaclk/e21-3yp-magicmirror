import os
import sys
import pyaudio
from dotenv import load_dotenv

# ================= LOAD ENVIRONMENT =================
load_dotenv()

# Ensure your Service Account key is pointed to correctly
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_PATH", "")

# ================= WINDOWS FIX =================
if sys.platform.startswith("win"):
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ================= AWS CONFIGURATION =================
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
BUCKET_NAME = os.getenv("BUCKET_NAME")
COLLECTION_ID = os.getenv("COLLECTION_ID")

# ================= GEMINI CONFIGURATION =================
GEMINI_PROJECT_ID = os.getenv("GEMINI_PROJECT_ID")
GOOGLE_APPLICATION_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_PATH")
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_LOCATION = os.getenv("GEMINI_LOCATION", "us-central1")

CUSTOM_PROMPT = (
    "You are Mirror Man, a smart mirror assistant. "
    "You must ALWAYS reply in natural language. "
    "Respond in the language same as the user, if the user speaks in Sinhala respond in Sinhala. "
    "Do NOT start your responses with greetings like 'Hello', 'Hi', or 'ආයුබෝවන්' unless the user is explicitly greeting you. "
    "Just answer the user's question directly and naturally. Keep responses short, warm, friendly, and easy to understand."
)

# ================= AUDIO SETTINGS (main app) =================
FORMAT = pyaudio.paInt16
CHANNELS = 1
HARDWARE_IN_RATE = 16000
HARDWARE_OUT_RATE = 24000
CHUNK = 1024

# ================= MUSIC ASSISTANT SETTINGS =================
ALSA_MIC_CARD = "plughw:2,0"
RECORD_SECONDS = 4
SAMPLE_RATE = 16000
MUSIC_CHANNELS = 1
VOICE = "en-GB-SoniaNeural"

# ================= SERIAL BRIDGE SETTINGS =================
SERIAL_PORT = "/dev/ttyUSB0"
SERIAL_BAUD = 115200
API_URL = "http://127.0.0.1:8000/api/presence/"
