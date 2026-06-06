import sys
import asyncio
import os
import pyaudio
import uvicorn
import webbrowser
import time
import threading
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
# Import config first (triggers load_dotenv and env setup)
from config import settings

from services.weather_service import get_current_weather

# ================= WINDOWS FIX =================
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Import components
from controllers.websocket_manager import manager
from controllers.routes import register_routes
from services.ai_bot import SinhalaBot
from services.s3_watcher import check_s3_inbox

# ================= INITIALIZE FASTAPI =================
app = FastAPI()

# Mount static files from the views directory
static_dir = os.path.join(os.path.dirname(__file__), "views", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ================= INITIALIZE BOT =================
pya = pyaudio.PyAudio()
bot = SinhalaBot()

# ================= REGISTER ROUTES =================
register_routes(app, bot, manager)

# ================= PERIODIC FACE INDEXING =================
async def run_periodic_face_indexing():
    """Runs face indexing periodically (every 10 minutes) in a non-blocking background thread."""
    from services.face_indexer import dynamic_indexing
    # Wait 10 seconds after startup before the first run to avoid congestion
    await asyncio.sleep(10)
    while True:
        try:
            print("🔄 [Face Indexer] Running periodic face indexing...", flush=True)
            await asyncio.to_thread(dynamic_indexing)
            print("✅ [Face Indexer] Periodic face indexing completed.", flush=True)
        except Exception as e:
            print(f"⚠️ [Face Indexer] Error in periodic indexing: {e}", flush=True)
        # Sleep for 10 minutes (600 seconds)
        await asyncio.sleep(600)


# ================= STARTUP EVENT =================
@app.on_event("startup")
async def startup_event():
    # Start both the Bot and the AWS Watcher alongside the Web Server!
    asyncio.create_task(bot.run())
    asyncio.create_task(check_s3_inbox())
    asyncio.create_task(run_periodic_face_indexing())

@app.on_event("shutdown")
async def shutdown_event():
    pya.terminate()


@app.get("/api/weather")
def weather_api():
    weather = get_current_weather()

    if weather is None:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "Weather data is currently unavailable"
            }
        )

    return {"status": "success", "data": weather}

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
    threading.Thread(target=open_browser, daemon=True).start()

    # Use host="127.0.0.1" so the logs show the correct clickable address
    uvicorn.run(app, host="127.0.0.1", port=8000)
