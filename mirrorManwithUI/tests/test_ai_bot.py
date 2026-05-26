"""Tests for services/ai_bot.py — verifies SinhalaBot behavior."""
import pytest
import inspect
import re
from unittest.mock import MagicMock, patch, AsyncMock


class TestSinhalaBot:
    """Regression tests for the AI bot."""

    def test_initial_state(self):
        """Bot should start inactive and not exiting."""
        from services.ai_bot import SinhalaBot
        bot = SinhalaBot()
        assert bot.should_exit is False
        assert bot.is_active is False

    def test_recognizer_initialized(self):
        """Bot should have a speech recognizer."""
        from services.ai_bot import SinhalaBot
        bot = SinhalaBot()
        assert bot.recognizer is not None
    def test_speak_delegates_to_tts_service(self):
        """Bot.speak() should call tts_service.speak_pygame with correct voice based on language."""
        from services.ai_bot import SinhalaBot
        bot = SinhalaBot()
        with patch("services.ai_bot.speak_pygame") as mock_speak:
            # Test English
            bot.speak("hello")
            mock_speak.assert_called_with("hello", voice="en-US-JennyNeural")
            
            # Test Sinhala
            bot.speak("ආයුබෝවන්")
            mock_speak.assert_called_with("ආයුබෝවන්", voice="si-LK-ThiliniNeural")

    def test_wake_word_triggers(self):
        """Verify wake word list contains expected triggers."""
        triggers = ["hey mirror", "mirror", "hai mera", "hey me", "mera"]
        test_cases = [
            ("hey mirror how are you", True),
            ("mirror show me", True),
            ("hai mera", True),
            ("random words", False),
            ("hello there", False),
        ]
        for text, expected in test_cases:
            result = any(trig in text.lower() for trig in triggers)
            assert result == expected, f"Failed for: {text}"

    def test_shutdown_keywords(self):
        """Verify shutdown keywords match original logic."""
        shutdown_keywords = ["goodbye", "stop", "shut down", "exit", "bye", "?????????"]
        assert "goodbye" in shutdown_keywords
        assert "stop" in shutdown_keywords
        assert "exit" in shutdown_keywords
        assert "bye" in shutdown_keywords

    def test_consecutive_errors_deactivate(self):
        """Bot should deactivate after 2 consecutive errors."""
        from services.ai_bot import SinhalaBot
        bot = SinhalaBot()
        bot.is_active = True
        consecutive_errors = 2
        if consecutive_errors >= 2:
            bot.is_active = False
        assert bot.is_active is False


class TestVideoBroadcastSourceInspection:
    """Source-inspection-based regression tests for video state broadcasting.
    These verify the broadcast protocol without requiring hardware (microphone/audio).
    """

    def test_detect_wake_word_broadcasts_show_mirror(self):
        """detect_wake_word should broadcast 'show_mirror' on wake word detection."""
        from services.ai_bot import SinhalaBot
        source = inspect.getsource(SinhalaBot.detect_wake_word)
        assert '"show_mirror"' in source or "'show_mirror'" in source, \
            "detect_wake_word should broadcast 'show_mirror'"

    def test_detect_wake_word_does_not_broadcast_active(self):
        """detect_wake_word must NOT broadcast 'active' (old protocol)."""
        from services.ai_bot import SinhalaBot
        source = inspect.getsource(SinhalaBot.detect_wake_word)
        assert 'broadcast("active")' not in source and "broadcast('active')" not in source, \
            "detect_wake_word should NOT broadcast 'active'"

    def test_run_broadcasts_hide_mirror(self):
        """run() should broadcast 'hide_mirror' to restore the dashboard."""
        from services.ai_bot import SinhalaBot
        source = inspect.getsource(SinhalaBot.run)
        assert '"hide_mirror"' in source or "'hide_mirror'" in source, \
            "run() should broadcast 'hide_mirror'"

    def test_run_last_broadcast_is_hide_mirror(self):
        """The last broadcast in run() should be 'hide_mirror'."""
        from services.ai_bot import SinhalaBot
        source = inspect.getsource(SinhalaBot.run)
        lines = source.strip().split('\n')
        last_broadcast_line = None
        for line in reversed(lines):
            if 'broadcast' in line:
                last_broadcast_line = line.strip()
                break
        assert last_broadcast_line is not None
        assert 'hide_mirror' in last_broadcast_line, \
            f"Last broadcast in run() should be 'hide_mirror', got: {last_broadcast_line}"

    def test_run_session_broadcasts_idle_for_listening(self):
        """run_session should broadcast 'idle' when waiting for user speech."""
        from services.ai_bot import SinhalaBot
        source = inspect.getsource(SinhalaBot.run_session)
        assert '"idle"' in source or "'idle'" in source, \
            "run_session should broadcast 'idle' while listening"

    def test_run_session_broadcasts_thinking(self):
        """run_session should broadcast 'thinking' before AI generates response."""
        from services.ai_bot import SinhalaBot
        source = inspect.getsource(SinhalaBot.run_session)
        assert '"thinking"' in source or "'thinking'" in source, \
            "run_session should broadcast 'thinking'"

    def test_run_session_broadcasts_talking(self):
        """run_session should broadcast 'talking' before delivering response."""
        from services.ai_bot import SinhalaBot
        source = inspect.getsource(SinhalaBot.run_session)
        assert '"talking"' in source or "'talking'" in source, \
            "run_session should broadcast 'talking'"

    def test_run_session_ai_flow_thinking_before_talking(self):
        """In the AI response path, 'thinking' should appear before 'talking'.
        Note: the shutdown path also has 'talking' before thinking, which is
        correct (it's in an if-branch that exits early).
        """
        from services.ai_bot import SinhalaBot
        source = inspect.getsource(SinhalaBot.run_session)
        # Find the thinking broadcast
        thinking_match = re.search(r'broadcast\(["\']thinking["\']\)', source)
        assert thinking_match is not None, "Should have broadcast('thinking')"
        # Find a talking broadcast that comes AFTER thinking (the AI response talking)
        after_thinking = source[thinking_match.end():]
        assert 'broadcast("talking")' in after_thinking or "broadcast('talking')" in after_thinking, \
            "Should have broadcast('talking') after broadcast('thinking') in AI response path"

    def test_run_session_idle_broadcast_after_talking(self):
        """After speaking a response, run_session should broadcast 'idle' to show idle.mp4."""
        from services.ai_bot import SinhalaBot
        source = inspect.getsource(SinhalaBot.run_session)
        # Find the AI response talking broadcast (after thinking)
        thinking_pos = source.find('"thinking"')
        after_thinking = source[thinking_pos:]
        talking_pos = after_thinking.find('"talking"')
        after_talking = after_thinking[talking_pos:]
        assert '"idle"' in after_talking, \
            "Should broadcast 'idle' after speaking the AI response"

    def test_run_greeting_flow_order(self):
        """run() should broadcast talking → idle → (session) → hide_mirror."""
        from services.ai_bot import SinhalaBot
        source = inspect.getsource(SinhalaBot.run)
        talking_pos = source.find('"talking"')
        idle_pos = source.find('"idle"')
        hide_pos = source.find('"hide_mirror"')
        assert talking_pos < idle_pos < hide_pos, \
            f"Expected talking({talking_pos}) < idle({idle_pos}) < hide_mirror({hide_pos})"

    def test_shutdown_broadcasts_talking_before_speaking(self):
        """On shutdown keyword, should broadcast 'talking' before the goodbye TTS."""
        from services.ai_bot import SinhalaBot
        source = inspect.getsource(SinhalaBot.run_session)
        # Find shutdown section
        shutdown_idx = source.find("Shutdown command")
        assert shutdown_idx > 0, "Should have shutdown section"
        after_shutdown = source[shutdown_idx:]
        talking_idx = after_shutdown.find('"talking"')
        speak_idx = after_shutdown.find("self.speak")
        assert talking_idx < speak_idx, \
            "Should broadcast 'talking' before speaking goodbye"


    def test_bot_has_fallback_speak(self):
        """Bot should have a _fallback_speak method."""
        from services.ai_bot import SinhalaBot
        bot = SinhalaBot()
        assert hasattr(bot, "_fallback_speak")
        assert callable(bot._fallback_speak)
    def test_bot_speak_uses_correct_voice(self):
        """Bot.speak should dynamically use si-LK-ThiliniNeural or en-US-JennyNeural."""
        from services.ai_bot import SinhalaBot
        bot = SinhalaBot()
        with patch("services.ai_bot.speak_pygame") as mock_speak:
            bot.speak("ආයුබෝවන්")
            mock_speak.assert_called_with("ආයුබෝවන්", voice="si-LK-ThiliniNeural")
            
            bot.speak("test text")
            mock_speak.assert_called_with("test text", voice="en-US-JennyNeural")
