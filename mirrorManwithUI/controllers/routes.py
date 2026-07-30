import os
import json
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse

from models.app_state import notifications, priority_schedule
from config.settings import BUCKET_NAME
from config.aws_config import get_s3_client


def register_routes(app, bot, manager):
    """Attach all HTTP and WebSocket routes to the FastAPI app."""

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
        elif os.path.exists("views/static/index.html"):
            return FileResponse("views/static/index.html")
        return HTMLResponse("<h1>index.html not found!</h1>")

    @app.get("/api/data")
    async def get_sensor_data():
        return {
            "weather": {"temp": 28, "humidity": 80, "description": "Partly Cloudy"},
            "priority_schedule": priority_schedule,
            "notifications": notifications
        }

    @app.get("/api/photos")
    async def get_photos():
        """List all photos in S3 public/slideshow/ and return presigned URLs."""
        try:
            s3 = get_s3_client()
            res = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix="public/slideshow/")

            photo_urls = []
            if "Contents" in res:
                for item in res["Contents"]:
                    key = item["Key"]
                    # Skip folder entries and non-image files
                    if key.endswith("/"):
                        continue
                    lower = key.lower()
                    if not (lower.endswith(".jpg") or lower.endswith(".jpeg")
                            or lower.endswith(".png") or lower.endswith(".webp")):
                        continue

                    # Generate a presigned URL valid for 1 hour
                    url = s3.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": BUCKET_NAME, "Key": key},
                        ExpiresIn=3600,
                    )
                    photo_urls.append({"key": key, "url": url})

            # Sort by key name (chronological for slide_<timestamp>.jpg naming)
            photo_urls.sort(key=lambda x: x["key"])

            return JSONResponse({"status": "success", "photos": photo_urls})

        except Exception as e:
            print(f"[WARNING] [Photos API] Error fetching photos from S3: {e}", flush=True)
            return JSONResponse(
                status_code=503,
                content={"status": "error", "message": str(e)}
            )

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await manager.connect(websocket)
        
        # MOCK PRESENCE SENSOR: Automatically tell the UI that someone is present
        # since we don't have the physical sensor running via serial_bridge.py
        await websocket.send_text(json.dumps({"type": "presence", "value": "present"}))

        if bot.is_active:
            await websocket.send_text("show_mirror")
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket)
            # If no browser tab is open anymore, stop the bot
            if len(manager.active_connections) == 0 and bot.is_active:
                print("[INFO] Last browser tab closed — stopping Mirror Man.", flush=True)
                bot.is_active = False
                bot.is_speaking = False
