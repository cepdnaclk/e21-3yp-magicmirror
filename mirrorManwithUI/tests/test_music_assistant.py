"""Tests for services/music_assistant.py — verifies command parsing and music control logic."""
import pytest
from unittest.mock import patch, MagicMock


class TestParseCommand:
    """Regression tests for the parse_command function.
    This is the core logic — every test case must match the original behavior.
    """

    @pytest.fixture(autouse=True)
    def import_parse_command(self):
        from services.music_assistant import parse_command
        self.parse_command = parse_command

    # ===== PLAY COMMANDS =====

    def test_play_with_song_name(self):
        action, song, is_sinhala = self.parse_command("play bohemian rhapsody")
        assert action == "play"
        assert song == "bohemian rhapsody"
        assert is_sinhala is False

    def test_play_alone_defaults_to_relaxing(self):
        action, song, is_sinhala = self.parse_command("play")
        assert action == "play"
        assert song == "relaxing music"

    def test_play_me_some(self):
        action, song, is_sinhala = self.parse_command("play me some jazz")
        assert action == "play"
        assert song == "jazz"

    def test_play_the(self):
        action, song, is_sinhala = self.parse_command("play the beatles")
        assert action == "play"
        assert song == "beatles"

    def test_play_sinhala_keyword(self):
        action, song, is_sinhala = self.parse_command("play sinhala hits")
        assert action == "play"
        assert is_sinhala is True

    def test_mirror_play(self):
        action, song, is_sinhala = self.parse_command("mirror play something")
        assert action == "play"

    # ===== STOP COMMANDS =====

    def test_stop_exact(self):
        action, song, is_sinhala = self.parse_command("stop")
        assert action == "stop"
        assert song is None

    def test_stop_music(self):
        action, song, is_sinhala = self.parse_command("stop music")
        assert action == "stop"

    def test_stop_playing(self):
        action, song, is_sinhala = self.parse_command("stop playing")
        assert action == "stop"

    def test_mirror_stop(self):
        action, song, is_sinhala = self.parse_command("mirror stop")
        assert action == "stop"

    # ===== PAUSE COMMANDS =====

    def test_pause_exact(self):
        action, song, is_sinhala = self.parse_command("pause")
        assert action == "pause"

    def test_pause_music(self):
        action, song, is_sinhala = self.parse_command("pause music")
        assert action == "pause"

    def test_mirror_pause(self):
        action, song, is_sinhala = self.parse_command("mirror pause")
        assert action == "pause"

    # ===== RESUME COMMANDS =====

    def test_resume_exact(self):
        action, song, is_sinhala = self.parse_command("resume")
        assert action == "resume"

    def test_resume_music(self):
        action, song, is_sinhala = self.parse_command("resume music")
        assert action == "resume"

    def test_continue_command(self):
        action, song, is_sinhala = self.parse_command("continue")
        assert action == "resume"

    def test_unpause_command(self):
        action, song, is_sinhala = self.parse_command("unpause")
        assert action == "resume"

    # ===== EXIT COMMANDS =====

    def test_exit_exact(self):
        action, song, is_sinhala = self.parse_command("exit")
        assert action == "exit"

    def test_quit_exact(self):
        action, song, is_sinhala = self.parse_command("quit")
        assert action == "exit"

    def test_goodbye_exact(self):
        action, song, is_sinhala = self.parse_command("goodbye")
        assert action == "exit"

    def test_shut_down(self):
        action, song, is_sinhala = self.parse_command("shut down")
        assert action == "exit"

    # ===== IGNORE (non-wake-word inputs) =====

    def test_random_speech_ignored(self):
        action, song, is_sinhala = self.parse_command("hello how are you")
        assert action == "ignore"

    def test_empty_string_ignored(self):
        action, song, is_sinhala = self.parse_command("")
        assert action == "ignore"

    def test_none_ignored(self):
        action, song, is_sinhala = self.parse_command(None)
        assert action == "ignore"

    def test_normal_conversation_ignored(self):
        action, song, is_sinhala = self.parse_command("what is the weather today")
        assert action == "ignore"

    # ===== MUSIC STATE =====

    def test_is_music_playing_when_no_process(self):
        from services import music_assistant
        music_assistant.ffplay_process = None
        assert music_assistant.is_music_playing() is False

    def test_is_music_playing_with_finished_process(self):
        from services import music_assistant
        mock_proc = MagicMock()
        mock_proc.poll.return_value = 0  # process finished
        music_assistant.ffplay_process = mock_proc
        assert music_assistant.is_music_playing() is False
        music_assistant.ffplay_process = None  # cleanup
