"""
Shared pytest fixtures for Mirror Man regression tests.
Mocks external dependencies (AWS, audio, Gemini) so tests run without hardware or cloud access.
"""
# pyrefly: ignore [missing-import]
import sys
import os
# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

# Ensure the mirrorManwithUI directory is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ================= MOCK PYAUDIO BEFORE ANY IMPORTS =================
# pyaudio requires PortAudio C library; mock it for CI/test environments
mock_pyaudio_module = MagicMock()
mock_pyaudio_module.paInt16 = 8  # real constant value
mock_pyaudio_instance = MagicMock()
mock_pyaudio_module.PyAudio.return_value = mock_pyaudio_instance
sys.modules["pyaudio"] = mock_pyaudio_module


# ================= MOCK PICAMERA2 =================
sys.modules["picamera2"] = MagicMock()

# ================= MOCK CV2 (OpenCV) =================
mock_cv2 = MagicMock()
sys.modules["cv2"] = mock_cv2

# ================= MOCK YT_DLP =================
mock_yt_dlp = MagicMock()
sys.modules["yt_dlp"] = mock_yt_dlp

# ================= MOCK EDGE_TTS =================
mock_edge_tts_module = MagicMock()
sys.modules["edge_tts"] = mock_edge_tts_module


# ================= MOCK PYGAME =================
mock_pygame = MagicMock()
mock_pygame.mixer.get_init.return_value = True
mock_pygame.mixer.music.get_busy.return_value = False
mock_pygame.time.Clock.return_value.tick = MagicMock()
sys.modules["pygame"] = mock_pygame


@pytest.fixture
def mock_s3_client():
    """Returns a mocked boto3 S3 client."""
    with patch("config.aws_config.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_rekognition_client():
    """Returns a mocked boto3 Rekognition client."""
    with patch("config.aws_config.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_gemini():
    """Mocks the Gemini genai client."""
    with patch("services.ai_bot.genai") as mock_genai:
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_edge_tts():
    """Mocks edge_tts for TTS tests."""
    with patch("services.tts_service.edge_tts") as mock_tts:
        yield mock_tts


@pytest.fixture
def websocket_manager():
    """Returns a fresh ConnectionManager instance."""
    from controllers.websocket_manager import ConnectionManager
    return ConnectionManager()
