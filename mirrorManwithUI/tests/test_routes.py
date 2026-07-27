"""Tests for controllers/routes.py — verifies FastAPI HTTP endpoints."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from controllers.routes import register_routes
from controllers.websocket_manager import ConnectionManager


@pytest.fixture
def test_app():
    """Creates a test FastAPI app with routes registered."""
    app = FastAPI()
    mock_bot = MagicMock()
    mock_bot.is_active = False
    test_manager = ConnectionManager()

    register_routes(app, mock_bot, test_manager)
    return app, mock_bot, test_manager


@pytest.fixture
def client(test_app):
    """Returns a TestClient for the test app."""
    app, _, _ = test_app
    return TestClient(app)


class TestRoutes:
    """Regression tests for HTTP routes."""

    def test_api_data_returns_weather(self, client):
        """GET /api/data should return weather, schedule, and notifications."""
        response = client.get("/api/data")
        assert response.status_code == 200
        data = response.json()
        assert "weather" in data
        assert "priority_schedule" in data
        assert "notifications" in data

    def test_api_data_weather_structure(self, client):
        """Weather data should have temp, humidity, description."""
        response = client.get("/api/data")
        weather = response.json()["weather"]
        assert "temp" in weather
        assert "humidity" in weather
        assert "description" in weather

    def test_presence_trigger_present(self, client):
        """GET /api/presence/present should return success."""
        response = client.get("/api/presence/present")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["received"] == "present"

    def test_presence_trigger_absent(self, client):
        """GET /api/presence/absent should return success."""
        response = client.get("/api/presence/absent")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["received"] == "absent"

    def test_root_returns_html_or_404(self, client):
        """GET / should return HTML content or a fallback message."""
        response = client.get("/")
        assert response.status_code == 200

    def test_api_data_schedule_is_list(self, client):
        """priority_schedule should be a list."""
        response = client.get("/api/data")
        data = response.json()
        assert isinstance(data["priority_schedule"], list)

    def test_api_data_notifications_is_list(self, client):
        """notifications should be a list."""
        response = client.get("/api/data")
        data = response.json()
        assert isinstance(data["notifications"], list)

    def test_websocket_sends_show_mirror_when_active(self, test_app):
        """WebSocket should send 'show_mirror' (not 'active') when bot is active on connect."""
        app, mock_bot, _ = test_app
        mock_bot.is_active = True
        client = TestClient(app)

        with client.websocket_connect("/ws") as ws:
            # First message is mock presence
            msg1 = ws.receive_text()
            # Second message should be show_mirror
            msg2 = ws.receive_text()
            assert msg2 == "show_mirror", f"Expected 'show_mirror', got '{msg2}'"

    def test_websocket_no_mirror_when_inactive(self, test_app):
        """WebSocket should NOT send 'show_mirror' when bot is inactive."""
        from models import app_state
        app_state.is_present = True
        app, mock_bot, _ = test_app
        mock_bot.is_active = False
        client = TestClient(app)

        with client.websocket_connect("/ws") as ws:
            # Should only receive the mock presence message
            msg1 = ws.receive_text()
            import json
            data = json.loads(msg1)
            assert data["type"] == "presence"
            assert data["value"] == "present"

    def test_websocket_disconnect_deactivates_bot_when_last_tab_closes(self, test_app):
        """When the last browser tab disconnects, the bot should be deactivated."""
        app, mock_bot, _ = test_app
        mock_bot.is_active = True
        mock_bot.is_speaking = True
        client = TestClient(app)

        with client.websocket_connect("/ws") as ws:
            ws.receive_text()  # consume presence message

        # After the tab closes (context manager exit), bot should be deactivated
        assert mock_bot.is_active is False
        assert mock_bot.is_speaking is False

    def test_websocket_disconnect_keeps_bot_active_if_another_tab_open(self, test_app):
        """If a second tab is still connected, closing one tab should NOT stop the bot."""
        app, mock_bot, test_manager = test_app
        mock_bot.is_active = True
        mock_bot.is_speaking = False
        client = TestClient(app)

        # Open two connections
        with client.websocket_connect("/ws") as ws1:
            ws1.receive_text()  # consume presence message
            with client.websocket_connect("/ws") as ws2:
                ws2.receive_text()  # consume presence message
                # Close the inner tab (ws2) — ws1 is still open
            # bot should still be active since ws1 is open
            assert mock_bot.is_active is True
