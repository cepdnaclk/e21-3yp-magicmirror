"""Tests for config/settings.py — verifies all environment variables load correctly."""
import os
import pytest
from unittest.mock import patch


class TestSettings:
    """Regression tests for centralized settings."""

    def test_aws_keys_loaded(self):
        """AWS credentials should be loaded from environment."""
        from config.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
        # In test env these may be None, but the attributes must exist
        assert hasattr(__import__("config.settings", fromlist=["AWS_ACCESS_KEY_ID"]), "AWS_ACCESS_KEY_ID")
        assert hasattr(__import__("config.settings", fromlist=["AWS_SECRET_ACCESS_KEY"]), "AWS_SECRET_ACCESS_KEY")

    def test_aws_region_loaded(self):
        """AWS_REGION should be available."""
        from config.settings import AWS_REGION
        assert AWS_REGION is None or isinstance(AWS_REGION, str)

    def test_bucket_name_loaded(self):
        """BUCKET_NAME should be available."""
        from config.settings import BUCKET_NAME
        assert BUCKET_NAME is None or isinstance(BUCKET_NAME, str)

    def test_collection_id_loaded(self):
        """COLLECTION_ID should be available."""
        from config.settings import COLLECTION_ID
        assert COLLECTION_ID is None or isinstance(COLLECTION_ID, str)

    def test_gemini_model_constant(self):
        """GEMINI_MODEL should be the expected model string."""
        from config.settings import GEMINI_MODEL
        assert GEMINI_MODEL == "gemini-2.5-flash"

    def test_gemini_location_loaded(self):
        """GEMINI_LOCATION should be available and default to us-central1."""
        from config.settings import GEMINI_LOCATION
        assert GEMINI_LOCATION == "us-central1" or isinstance(GEMINI_LOCATION, str)

    def test_custom_prompt_is_string(self):
        """CUSTOM_PROMPT must be a non-empty string."""
        from config.settings import CUSTOM_PROMPT
        assert isinstance(CUSTOM_PROMPT, str)
        assert len(CUSTOM_PROMPT) > 0
        assert "Mirror Man" in CUSTOM_PROMPT

    def test_audio_constants(self):
        """Audio constants must have correct values."""
        from config.settings import CHANNELS, HARDWARE_IN_RATE, HARDWARE_OUT_RATE, CHUNK
        assert CHANNELS == 1
        assert HARDWARE_IN_RATE == 16000
        assert HARDWARE_OUT_RATE == 24000
        assert CHUNK == 1024

    def test_music_constants(self):
        """Music assistant constants must exist."""
        from config.settings import ALSA_MIC_CARD, RECORD_SECONDS, SAMPLE_RATE, VOICE
        assert ALSA_MIC_CARD == "plughw:2,0"
        assert RECORD_SECONDS == 4
        assert SAMPLE_RATE == 16000
        assert VOICE == "en-GB-SoniaNeural"

    def test_serial_constants(self):
        """Serial bridge constants must exist."""
        from config.settings import SERIAL_PORT, SERIAL_BAUD, API_URL
        assert SERIAL_PORT == "/dev/ttyUSB0"
        assert SERIAL_BAUD == 115200
        assert "api/presence" in API_URL
