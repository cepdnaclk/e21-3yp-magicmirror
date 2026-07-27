import sys
import asyncio
import json
import os
import uvicorn
import webbrowser
import time
import threading
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
# Import config first (triggers load_dotenv and env setup)
from config import settings

import logging

class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return "/api/presence/status" not in msg and "/api/bot/status" not in msg

# Filter out status polling requests from console output
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

from services.weather_service import get_current_weather

# ================= WINDOWS FIX =================
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import components
from controllers.websocket_manager import manager
from controllers.routes import register_routes
from services.s3_watcher import check_s3_inbox

# ================= INITIALIZE FASTAPI =================
app = FastAPI()

# Mount static files from the views directory
static_dir = os.path.join(os.path.dirname(__file__), "views", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ================= REGISTER ROUTES =================
# Bot is now a separate process — pass None; routes.py will handle gracefully
register_routes(app, bot=None, manager=manager)

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
    # S3 watcher + face indexer run inside the server (no native-lib risk)
    # Bot is launched as a SEPARATE PROCESS by launcher.py to isolate PyAudio
    asyncio.create_task(check_s3_inbox())
    asyncio.create_task(run_periodic_face_indexing())

@app.on_event("shutdown")
async def shutdown_event():
    pass  # cleanup hook for future use


# ================= INTERNAL BROADCAST API =================
# Used by the bot_runner process to relay messages to WebSocket clients
@app.post("/api/internal/broadcast")
async def internal_broadcast(request: Request):
    """Receive a JSON payload from the bot process and broadcast to all WebSocket clients."""
    try:
        payload = await request.json()
        await manager.broadcast(json.dumps(payload))
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


# ================= INTERNAL BOT STATUS API =================
@app.get("/api/bot/status")
async def get_bot_status():
    from models import app_state
    return {
        "is_active": app_state.is_bot_active,
        "is_speaking": app_state.is_bot_speaking
    }

@app.post("/api/bot/status")
async def post_bot_status(request: Request):
    from models import app_state
    try:
        payload = await request.json()
        if "is_active" in payload:
            app_state.is_bot_active = payload["is_active"]
        if "is_speaking" in payload:
            app_state.is_bot_speaking = payload["is_speaking"]
        return {"status": "success"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})



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
    print("🪞 Starting Mirror Man OS...")

    # Define the local URL
    url = "http://127.0.0.1:8000"

    # This function opens the browser after a 2-second delay
    # to ensure the server has time to start up.
    def open_browser():
        time.sleep(2)
        print(f"🌐 Auto-opening dashboard at {url}")
        webbrowser.open(url)

    # We start the browser-opener in a separate thread
    # so it doesn't block the Uvicorn server startup.
    threading.Thread(target=open_browser, daemon=True).start()

    # Use host="127.0.0.1" so the logs show the correct clickable address
    uvicorn.run(app, host="127.0.0.1", port=8000)
