"""Tests for controllers/websocket_manager.py — verifies WebSocket connection management."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock


class TestConnectionManager:
    """Regression tests for WebSocket ConnectionManager."""

    def test_initial_state(self, websocket_manager):
        """Manager should start with no connections."""
        assert len(websocket_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_connect_adds_websocket(self, websocket_manager):
        """connect() should accept and store the websocket."""
        mock_ws = AsyncMock()
        await websocket_manager.connect(mock_ws)
        assert mock_ws in websocket_manager.active_connections
        mock_ws.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_removes_websocket(self, websocket_manager):
        """disconnect() should remove the websocket from active list."""
        mock_ws = AsyncMock()
        await websocket_manager.connect(mock_ws)
        websocket_manager.disconnect(mock_ws)
        assert mock_ws not in websocket_manager.active_connections

    def test_disconnect_nonexistent_is_safe(self, websocket_manager):
        """disconnect() on a non-connected websocket should not raise."""
        mock_ws = AsyncMock()
        websocket_manager.disconnect(mock_ws)  # should not raise

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all(self, websocket_manager):
        """broadcast() should send message to all connected websockets."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        await websocket_manager.connect(ws1)
        await websocket_manager.connect(ws2)

        await websocket_manager.broadcast("test message")

        ws1.send_text.assert_called_once_with("test message")
        ws2.send_text.assert_called_once_with("test message")

    @pytest.mark.asyncio
    async def test_broadcast_handles_failed_connection(self, websocket_manager):
        """broadcast() should not crash if one connection fails."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws1.send_text.side_effect = Exception("Connection lost")

        await websocket_manager.connect(ws1)
        await websocket_manager.connect(ws2)

        await websocket_manager.broadcast("test")
        # ws2 should still receive the message
        ws2.send_text.assert_called_once_with("test")
