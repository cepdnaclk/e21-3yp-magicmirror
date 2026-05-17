"""Tests for services/vision_engine.py — verifies alert structure and detection flow."""
import pytest
import json
import sys
from unittest.mock import MagicMock, patch
from datetime import datetime


class TestVisionEngine:
    """Regression tests for vision engine."""

    def test_send_alert_to_app_structure(self):
        """Alert JSON should have required fields."""
        # Need to mock s3 before importing
        mock_s3 = MagicMock()
        with patch.dict("sys.modules", {}):
            from services.vision_engine import send_alert_to_app
            # Patch the module-level s3 client
            with patch("services.vision_engine.s3", mock_s3):
                send_alert_to_app("thenuka", "SAD")

                # Verify S3 put_object was called
                mock_s3.put_object.assert_called_once()
                call_kwargs = mock_s3.put_object.call_args[1]

                # Verify content type
                assert call_kwargs["ContentType"] == "application/json"

                # Verify JSON body structure
                body = json.loads(call_kwargs["Body"])
                assert body["user_id"] == "thenuka"
                assert body["emotion"] == "SAD"
                assert "time" in body
                assert "message" in body
                assert body["status"] == "unread"

    def test_alert_message_format(self):
        """Alert message should include person name and emotion."""
        from services.vision_engine import send_alert_to_app
        mock_s3 = MagicMock()
        with patch("services.vision_engine.s3", mock_s3):
            send_alert_to_app("john", "ANGRY")
            call_kwargs = mock_s3.put_object.call_args[1]
            body = json.loads(call_kwargs["Body"])
            assert "john" in body["message"]
            assert "ANGRY" in body["message"]

    def test_alert_s3_key_format(self):
        """Alert should be uploaded to public/alerts/ prefix."""
        mock_s3 = MagicMock()
        with patch("services.vision_engine.s3", mock_s3):
            from services.vision_engine import send_alert_to_app
            send_alert_to_app("user1", "FEAR")
            key = mock_s3.put_object.call_args[1]["Key"]
            assert key.startswith("public/alerts/alert_user1_")
            assert key.endswith(".json")

    def test_negative_emotions_list(self):
        """Vision engine should alert on SAD, ANGRY, FEAR only."""
        import inspect
        from services.vision_engine import run_vision
        source = inspect.getsource(run_vision)
        assert '"SAD"' in source
        assert '"ANGRY"' in source
        assert '"FEAR"' in source

    def test_run_vision_is_callable(self):
        """run_vision function should exist and be callable."""
        from services.vision_engine import run_vision
        assert callable(run_vision)
