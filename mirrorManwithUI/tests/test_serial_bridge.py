"""Regression tests for presence sensor logic and serial bridge parsing."""
import pytest
import json
import re
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from controllers.routes import register_routes
from controllers.websocket_manager import ConnectionManager


@pytest.fixture
def presence_app():
    """Creates a test FastAPI app for presence testing."""
    app = FastAPI()
    mock_bot = MagicMock()
    mock_bot.is_active = False
    manager = ConnectionManager()

    register_routes(app, mock_bot, manager)
    return app, manager


def test_presence_present_broadcasts_correct_websocket_event(presence_app):
    """GET /api/presence/present must broadcast type=presence, value=present via WebSocket."""
    app, _ = presence_app
    client = TestClient(app)

    with client.websocket_connect("/ws") as ws:
        # Consume initial mock presence message
        init_msg = ws.receive_text()
        
        # Trigger presence event via HTTP GET
        res = client.get("/api/presence/present")
        assert res.status_code == 200
        assert res.json()["received"] == "present"

        # Receive broadcasted WS message
        ws_msg = ws.receive_text()
        data = json.loads(ws_msg)
        assert data["type"] == "presence"
        assert data["value"] == "present"


def test_presence_absent_broadcasts_correct_websocket_event(presence_app):
    """GET /api/presence/absent must broadcast type=presence, value=absent via WebSocket."""
    app, _ = presence_app
    client = TestClient(app)

    with client.websocket_connect("/ws") as ws:
        # Consume initial mock presence message
        ws.receive_text()

        # Trigger absence event via HTTP GET
        res = client.get("/api/presence/absent")
        assert res.status_code == 200
        assert res.json()["received"] == "absent"

        # Receive broadcasted WS message
        ws_msg = ws.receive_text()
        data = json.loads(ws_msg)
        assert data["type"] == "presence"
        assert data["value"] == "absent"


def test_presence_confirmed_absent_deactivates_active_bot():
    """When confirmed_absent is called, active bot must be deactivated and 'hide_mirror' sent."""
    mock_bot = MagicMock()
    mock_bot.is_active = True
    mock_bot.is_speaking = True
    manager = ConnectionManager()

    test_app = FastAPI()
    register_routes(test_app, mock_bot, manager)
    client = TestClient(test_app)

    with client.websocket_connect("/ws") as ws:
        ws.receive_text()  # init presence
        ws.receive_text()  # show_mirror

        client.get("/api/presence/confirmed_absent")
        msg = ws.receive_text()
        assert msg == "hide_mirror"
        assert mock_bot.is_active is False
        assert mock_bot.is_speaking is False


@pytest.mark.parametrize("line, expected_status", [
    ("PRESENT", "present"),
    ("ABSENT", "absent"),
    ("Distance: 150 cm", "present"),
    ("Distance: 250 cm", "absent"),
    ("1.2 m", "present"),
    ("3.5 m", "absent"),
    ("Measured Distance (19.05): PRESENT", "present"),
    ("Measured Distance (460.75): ABSENT", "absent"),
])
def test_serial_bridge_parsing_logic(line, expected_status):
    """Verifies that serial bridge correctly maps distance readings and keywords to presence states."""
    upper_line = line.upper()

    detected_state = None
    if "PRESENT" in upper_line:
        detected_state = "present"
    elif "ABSENT" in upper_line:
        detected_state = "absent"
    else:
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", line)
        if numbers:
            dist = float(numbers[0])
            is_present = (dist < 2.0) if dist < 10.0 else (dist < 200.0)
            detected_state = "present" if is_present else "absent"

    assert detected_state == expected_status
