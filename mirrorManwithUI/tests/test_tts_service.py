"""Tests for services/tts_service.py — verifies TTS functions."""
# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import patch, MagicMock


class TestTTSService:
    """Regression tests for TTS service."""

    def test_speak_pygame_is_callable(self):
        """speak_pygame function should be importable and callable."""
        from services.tts_service import speak_pygame
        assert callable(speak_pygame)

    def test_fallback_speak_is_callable(self):
        """fallback_speak function should be importable and callable."""
        from services.tts_service import fallback_speak
        assert callable(fallback_speak)

    @pytest.mark.asyncio
    async def test_speak_ffplay_is_async(self):
        """speak_ffplay should be an async function."""
        import asyncio
        from services.tts_service import speak_ffplay
        assert asyncio.iscoroutinefunction(speak_ffplay)

    def test_speak_pygame_default_voice(self):
        """speak_pygame should accept a voice parameter."""
        import inspect
        from services.tts_service import speak_pygame
        sig = inspect.signature(speak_pygame)
        assert "voice" in sig.parameters
        assert sig.parameters["voice"].default == "si-LK-ThiliniNeural"

    @pytest.mark.asyncio
    async def test_speak_ffplay_default_voice(self):
        """speak_ffplay should have default voice of en-GB-SoniaNeural."""
        import inspect
        from services.tts_service import speak_ffplay
        sig = inspect.signature(speak_ffplay)
        assert "voice" in sig.parameters
        assert sig.parameters["voice"].default == "en-GB-SoniaNeural"
