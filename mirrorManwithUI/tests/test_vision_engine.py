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
        mock_s3 = MagicMock()
        from services.vision_engine import send_alert_to_app
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
        mock_s3 = MagicMock()
        from services.vision_engine import send_alert_to_app
        with patch("services.vision_engine.s3", mock_s3):
            send_alert_to_app("john", "ANGRY")
            call_kwargs = mock_s3.put_object.call_args[1]
            body = json.loads(call_kwargs["Body"])
            assert "john" in body["message"]
            assert "ANGRY" in body["message"]

    def test_alert_s3_key_format(self):
        """Alert should be uploaded to public/alerts/{userId}/ sub-folder."""
        mock_s3 = MagicMock()
        from services.vision_engine import send_alert_to_app
        with patch("services.vision_engine.s3", mock_s3):
            send_alert_to_app("user1", "FEAR")
            key = mock_s3.put_object.call_args[1]["Key"]
            # New targeted format: public/alerts/{userId}/alert_{timestamp}.json
            assert key.startswith("public/alerts/user1/alert_")
            assert key.endswith(".json")

    def test_alert_multi_owner_distribution(self):
        """Alert should be sent to all matching owners found in DynamoDB."""
        mock_s3 = MagicMock()
        from services.vision_engine import send_alert_to_app
        
        # Mock get_family_member_owners to return multiple email addresses
        mock_owners = ["john@gmail.com", "mary@gmail.com"]
        with patch("services.vision_engine.get_family_member_owners", return_value=mock_owners), \
             patch("services.vision_engine.s3", mock_s3):
            
            send_alert_to_app("sithu_Owner_Self", "SAD")
            
            # Should call put_object twice (once for each owner)
            assert mock_s3.put_object.call_count == 2
            
            # Verify the keys are constructed correctly for each owner
            call_args_list = mock_s3.put_object.call_args_list
            keys = [call[1]["Key"] for call in call_args_list]
            
            assert any(k.startswith("public/alerts/john/alert_") for k in keys)
            assert any(k.startswith("public/alerts/mary/alert_") for k in keys)

    def test_negative_emotions_list(self):
        """Vision engine should alert on SAD, ANGRY, FEAR only."""
        import inspect
        from services.vision_engine import process_image
        source = inspect.getsource(process_image)
        assert '"SAD"' in source
        assert '"ANGRY"' in source
        assert '"FEAR"' in source

    def test_run_vision_is_callable(self):
        """run_vision function should exist and be callable."""
        from services.vision_engine import run_vision
        assert callable(run_vision)

    def test_process_image_is_callable(self):
        """process_image function should exist and be callable."""
        from services.vision_engine import process_image
        assert callable(process_image)
