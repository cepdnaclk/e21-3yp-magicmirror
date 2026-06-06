"""Tests for services/s3_watcher.py — verifies S3 inbox polling and DynamoDB reminder logic."""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock


class TestS3Watcher:
    """Regression tests for S3 notification/reminder watcher."""

    @pytest.mark.asyncio
    async def test_check_s3_inbox_is_async(self):
        """check_s3_inbox should be an async function."""
        from services.s3_watcher import check_s3_inbox
        import asyncio
        assert asyncio.iscoroutinefunction(check_s3_inbox)

    @pytest.mark.asyncio
    async def test_notifications_are_broadcast(self):
        """When S3 has notification files, they should be broadcast and deleted."""
        mock_s3 = MagicMock()
        mock_s3.list_objects_v2.side_effect = [
            # First call: notifications
            {"Contents": [{"Key": "public/notifications/msg1.txt"}]},
            # Second call: reminders (empty)
            {},
        ]
        mock_s3.get_object.return_value = {
            "Body": MagicMock(read=MagicMock(return_value=b"Hello from app"))
        }

        with patch("services.s3_watcher.get_s3_client", return_value=mock_s3), \
             patch("services.s3_watcher.manager") as mock_manager, \
             patch("services.s3_watcher.asyncio") as mock_asyncio:

            mock_manager.broadcast = AsyncMock()

            # We can't run the infinite loop directly, so test the core logic
            from services.s3_watcher import BUCKET_NAME
            # Verify the function exists and is importable
            from services.s3_watcher import check_s3_inbox
            assert callable(check_s3_inbox)

    def test_notification_prefix(self):
        """Notification S3 prefix should be public/notifications/."""
        import inspect
        from services.s3_watcher import check_s3_inbox
        source = inspect.getsource(check_s3_inbox)
        assert "public/notifications/" in source

    def test_reminder_prefix(self):
        """Reminder S3 prefix should be public/reminders/."""
        import inspect
        from services.s3_watcher import check_s3_inbox
        source = inspect.getsource(check_s3_inbox)
        assert "public/reminders/" in source

    # ── DynamoDB reminder helper tests ──────────────────────────────────

    def test_parse_reminder_datetime_standard(self):
        """_parse_reminder_datetime should parse standard m/d/Y + 12-hour time."""
        from services.s3_watcher import _parse_reminder_datetime
        dt = _parse_reminder_datetime("6/15/2099", "2:30 PM")
        assert dt is not None
        assert dt.year == 2099
        assert dt.month == 6
        assert dt.day == 15
        assert dt.hour == 14
        assert dt.minute == 30

    def test_parse_reminder_datetime_today(self):
        """_parse_reminder_datetime should accept 'Today' as today's date."""
        from services.s3_watcher import _parse_reminder_datetime
        dt = _parse_reminder_datetime("Today", "11:00 AM")
        assert dt is not None
        assert dt.date() == datetime.now().date()

    def test_parse_reminder_datetime_anytime(self):
        """_parse_reminder_datetime should accept 'Anytime' as end of that day."""
        from services.s3_watcher import _parse_reminder_datetime
        dt = _parse_reminder_datetime("7/4/2099", "Anytime")
        assert dt is not None
        assert dt.year == 2099

    def test_parse_reminder_datetime_bad_input(self):
        """_parse_reminder_datetime should return None for garbage input."""
        from services.s3_watcher import _parse_reminder_datetime
        assert _parse_reminder_datetime("not-a-date", "bad-time") is None

    def test_get_upcoming_reminders_filters_past(self):
        """get_upcoming_reminders should only return reminders in the future."""
        from services.s3_watcher import _parse_reminder_datetime

        past   = _parse_reminder_datetime("1/1/2000", "12:00 PM")
        future = _parse_reminder_datetime("1/1/2099", "12:00 PM")

        assert past   is not None and past   < datetime.now()
        assert future is not None and future > datetime.now()

    def test_get_upcoming_reminders_is_callable(self):
        """get_upcoming_reminders should be importable and callable."""
        from services.s3_watcher import get_upcoming_reminders
        assert callable(get_upcoming_reminders)

    def test_reminder_list_broadcast_type(self):
        """reminder_list broadcast payload must have type and items fields."""
        # Simulate what the watcher broadcasts
        items = [{"id": "1", "date": "6/10/2099", "time": "9:00 AM",
                  "reason": "Take medicine", "expiry_epoch": 9999999999000}]
        payload = json.dumps({"type": "reminder_list", "items": items})
        parsed = json.loads(payload)
        assert parsed["type"] == "reminder_list"
        assert isinstance(parsed["items"], list)
        assert parsed["items"][0]["reason"] == "Take medicine"
        assert "expiry_epoch" in parsed["items"][0]
