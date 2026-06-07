import os
import json
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse

from models.app_state import notifications, priority_schedule


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
