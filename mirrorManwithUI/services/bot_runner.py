"""
Bot Runner — Runs the SinhalaBot in a SEPARATE PROCESS.

This isolates PyAudio/PortAudio (used by speech_recognition.Microphone) from
the FastAPI UI server.  If PyAudio segfaults, only this process dies — the
web dashboard keeps running.

Communication with the FastAPI server is done over HTTP:
  • Presence status  → GET  /api/presence/status
  • WebSocket broadcast → POST /api/internal/broadcast
  • Music commands   → imported directly (no PyAudio dependency)
"""

import asyncio
import json
import sys
import os
import time
import requests

# Add parent directory to path so we can import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings  # noqa: E402 — triggers dotenv loading

SERVER_URL = "http://127.0.0.1:8000"

# Shared session with cache-busting headers so we never get a 304
_session = requests.Session()
_session.headers.update({
    "Cache-Control": "no-cache, no-store",
    "Pragma": "no-cache",
})


# ─────────────────────────────────────────────────────────────
# Remote bridge — replaces direct app_state / manager access
# ─────────────────────────────────────────────────────────────

class _RemoteAppState:
    """Drop-in replacement for models.app_state that reads via HTTP."""

    @property
    def is_present(self):
        try:
            r = _session.get(f"{SERVER_URL}/api/presence/status", timeout=1)
            if r.status_code in (200, 304):
                # 304 means the server says "not changed" — reuse last known value
                if r.status_code == 200:
                    return r.json().get("is_present", False)
                # For 304, fall through and return current module value
                return _real_app_state_module.is_present if hasattr(_real_app_state_module, 'is_present') else False
        except Exception as e:
            print(f"[BotRunner] ⚠️ Presence check failed: {e}", flush=True)
        return False

    @is_present.setter
    def is_present(self, value):
        # The serial bridge sets presence via API; bot never writes this.
        pass


class _RemoteManager:
    """Drop-in replacement for ConnectionManager that broadcasts via HTTP."""

    @property
    def active_connections(self):
        # Used only for len() check when browser disconnects.
        # In the separate-process model we can't track this; return a
        # non-empty sentinel so the bot never thinks "last tab closed".
        return [True]

    async def broadcast(self, message: str):
        """POST the message to the FastAPI server for relay to WebSocket clients."""
        try:
            payload = json.loads(message) if isinstance(message, str) else message
            await asyncio.to_thread(
                requests.post,
                f"{SERVER_URL}/api/internal/broadcast",
                json=payload,
                timeout=2,
            )
        except Exception as e:
            print(f"⚠️  [BotRunner] Broadcast failed: {e}", flush=True)

    async def connect(self, ws):
        pass

    def disconnect(self, ws):
        pass


# ─────────────────────────────────────────────────────────────
# Monkey-patch modules BEFORE importing ai_bot
# ─────────────────────────────────────────────────────────────

import models.app_state as _real_app_state_module       # noqa: E402
import controllers.websocket_manager as _real_ws_module  # noqa: E402

_remote_state = _RemoteAppState()
_remote_mgr = _RemoteManager()

# Patch the module-level objects so ai_bot.py sees our remote versions
_real_app_state_module.is_present = False  # initial value; property reads via HTTP
_real_ws_module.manager = _remote_mgr

# Now import the bot (it will bind to our patched manager)
from services.ai_bot import SinhalaBot  # noqa: E402


class RemoteSinhalaBot(SinhalaBot):
    """Thin wrapper that overrides attribute access to use the HTTP bridge."""

    def __init__(self):
        self._is_active = False
        self._is_speaking = False
        super().__init__()

    @property
    def is_active(self):
        try:
            r = requests.get(f"{SERVER_URL}/api/bot/status", timeout=0.5)
            if r.status_code == 200:
                self._is_active = r.json().get("is_active", self._is_active)
        except Exception:
            pass
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        self._is_active = value
        try:
            requests.post(f"{SERVER_URL}/api/bot/status", json={"is_active": value}, timeout=0.5)
        except Exception:
            pass

    @property
    def is_speaking(self):
        try:
            r = requests.get(f"{SERVER_URL}/api/bot/status", timeout=0.5)
            if r.status_code == 200:
                self._is_speaking = r.json().get("is_speaking", self._is_speaking)
        except Exception:
            pass
        return self._is_speaking

    @is_speaking.setter
    def is_speaking(self, value):
        self._is_speaking = value
        try:
            requests.post(f"{SERVER_URL}/api/bot/status", json={"is_speaking": value}, timeout=0.5)
        except Exception:
            pass

    async def detect_wake_word(self):
        # Override the app_state.is_present check to use HTTP
        # The parent method reads `app_state.is_present` which is a module
        # attribute.  We patch it on every loop tick.
        _real_app_state_module.is_present = _remote_state.is_present
        await super().detect_wake_word()

    async def run_session(self):
        _real_app_state_module.is_present = _remote_state.is_present
        await super().run_session()

    async def run(self):
        """Main loop — keeps patching presence before each cycle."""
        while not self.should_exit:
            # Keep presence state synced
            _real_app_state_module.is_present = _remote_state.is_present

            await self.detect_wake_word()
            if self.is_active:
                await _remote_mgr.broadcast(
                    json.dumps({"type": "video", "state": "talking"})
                )
                await asyncio.to_thread(self.speak, "Hello! How can I help you?")
                await _remote_mgr.broadcast(
                    json.dumps({"type": "video", "state": "idle"})
                )
                self.conversation_history.clear()
                print("🧹 Conversation history cleared for new session.", flush=True)
                await self.run_session()
                print("🔙 Returning to dashboard...", flush=True)
                await _remote_mgr.broadcast(
                    json.dumps({"type": "mirror_hide", "status": "sleep"})
                )


# ─────────────────────────────────────────────────────────────
# Presence state sync background task
# ─────────────────────────────────────────────────────────────

async def _sync_presence_loop():
    """Continuously sync presence from the server into the patched module."""
    last_logged = None
    while True:
        try:
            val = _remote_state.is_present
            _real_app_state_module.is_present = val
            # Only log when the value changes to avoid spam
            if val != last_logged:
                print(f"[BotRunner] Presence synced: {'PRESENT' if val else 'ABSENT'}", flush=True)
                last_logged = val
        except Exception as e:
            print(f"[BotRunner] ⚠️ Sync error: {e}", flush=True)
        await asyncio.sleep(0.5)


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────

async def _main():
    print("🤖 [BotRunner] Starting AI Bot in isolated process...", flush=True)

    # Wait for the FastAPI server to be ready
    for attempt in range(30):
        try:
            r = requests.get(f"{SERVER_URL}/api/presence/status", timeout=1)
            if r.status_code == 200:
                print("🤖 [BotRunner] FastAPI server is ready.", flush=True)
                break
        except Exception:
            pass
        await asyncio.sleep(1)
    else:
        print("❌ [BotRunner] FastAPI server not reachable after 30s. Exiting.", flush=True)
        return

    bot = RemoteSinhalaBot()

    # Start background presence sync + bot together
    await asyncio.gather(
        _sync_presence_loop(),
        bot.run(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        print("\n🛑 [BotRunner] Stopped.", flush=True)
