"""Tests for models/app_state.py — verifies shared state structure."""
# pyrefly: ignore [missing-import]
import pytest


class TestAppState:
    """Regression tests for shared application state."""

    def test_notifications_is_list(self):
        """notifications should be an initially empty list."""
        from models.app_state import notifications
        assert isinstance(notifications, list)

    def test_priority_schedule_is_list(self):
        """priority_schedule should be a list (starts empty; populated live from DynamoDB)."""
        from models.app_state import priority_schedule
        assert isinstance(priority_schedule, list)

    def test_schedule_item_structure(self):
        """Each schedule item must have time, name/reason, and date keys (skipped when empty)."""
        from models.app_state import priority_schedule
        for item in priority_schedule:
            assert "time" in item
            # DynamoDB reminders use 'reason'; legacy items use 'name'
            assert "reason" in item or "name" in item
            assert "date" in item

    def test_notifications_mutable(self):
        """notifications list should be mutable (append/clear)."""
        from models.app_state import notifications
        original_len = len(notifications)
        notifications.append("test")
        assert len(notifications) == original_len + 1
        notifications.pop()  # cleanup
        assert len(notifications) == original_len
