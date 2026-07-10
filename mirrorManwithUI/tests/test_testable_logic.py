from datetime import datetime, timedelta

import pytest

from services.testable_logic import (
    classify_voice_command,
    should_hide_notification,
    should_send_emotion_alert,
    validate_reminder,
)


# -------------------------------------------------
# E/21/287 - Voice command tests
# -------------------------------------------------

@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("Hello Mirror", "ACTIVATE_MIRROR_MAN"),
        (" hello mirror ", "ACTIVATE_MIRROR_MAN"),
        ("Good bye", "DEACTIVATE_MIRROR_MAN"),
        ("goodbye", "DEACTIVATE_MIRROR_MAN"),
        ("Play Perfect", "PLAY_MUSIC"),
        ("pause music", "PAUSE_MUSIC"),
        ("resume music", "RESUME_MUSIC"),
        ("stop music", "STOP_MUSIC"),
        ("open calendar", "UNKNOWN"),
    ],
)
def test_classify_voice_command(command, expected):
    assert classify_voice_command(command) == expected


def test_voice_command_rejects_empty_input():
    with pytest.raises(ValueError):
        classify_voice_command("")


def test_voice_command_rejects_empty_song_name():
    with pytest.raises(ValueError):
        classify_voice_command("Play ")


def test_voice_command_rejects_invalid_type():
    with pytest.raises(TypeError):
        classify_voice_command(None)


# -------------------------------------------------
# E/21/229 - Reminder validation tests
# -------------------------------------------------

def test_valid_future_reminder():
    now = datetime(2026, 7, 10, 10, 0, 0)
    scheduled = now + timedelta(days=1)

    assert validate_reminder("Take medicine", scheduled, now) is True


def test_reminder_one_second_in_future():
    now = datetime(2026, 7, 10, 10, 0, 0)
    scheduled = now + timedelta(seconds=1)

    assert validate_reminder("Take medicine", scheduled, now) is True


def test_reminder_rejects_exact_current_time():
    now = datetime(2026, 7, 10, 10, 0, 0)

    with pytest.raises(ValueError):
        validate_reminder("Take medicine", now, now)


def test_reminder_rejects_past_time():
    now = datetime(2026, 7, 10, 10, 0, 0)
    scheduled = now - timedelta(seconds=1)

    with pytest.raises(ValueError):
        validate_reminder("Take medicine", scheduled, now)


@pytest.mark.parametrize("message", ["", "   "])
def test_reminder_rejects_empty_message(message):
    now = datetime(2026, 7, 10, 10, 0, 0)

    with pytest.raises(ValueError):
        validate_reminder(
            message,
            now + timedelta(hours=1),
            now,
        )


def test_reminder_accepts_200_character_message():
    now = datetime(2026, 7, 10, 10, 0, 0)
    message = "A" * 200

    assert validate_reminder(
        message,
        now + timedelta(hours=1),
        now,
    ) is True


def test_reminder_rejects_201_character_message():
    now = datetime(2026, 7, 10, 10, 0, 0)
    message = "A" * 201

    with pytest.raises(ValueError):
        validate_reminder(
            message,
            now + timedelta(hours=1),
            now,
        )


def test_reminder_rejects_invalid_message_type():
    now = datetime(2026, 7, 10, 10, 0, 0)

    with pytest.raises(TypeError):
        validate_reminder(
            None,
            now + timedelta(hours=1),
            now,
        )


# -------------------------------------------------
# E/21/055 - Notification visibility tests
# -------------------------------------------------

@pytest.mark.parametrize(
    ("presence", "elapsed", "expected"),
    [
        (True, 14.99, False),
        (True, 15, True),
        (True, 15.01, True),
        (False, 15, False),
        (False, 100, False),
        (True, 0, False),
    ],
)
def test_should_hide_notification(presence, elapsed, expected):
    assert should_hide_notification(presence, elapsed) is expected


def test_notification_rejects_negative_time():
    with pytest.raises(ValueError):
        should_hide_notification(True, -1)


def test_notification_rejects_invalid_presence_type():
    with pytest.raises(TypeError):
        should_hide_notification("yes", 15)


def test_notification_rejects_invalid_time_type():
    with pytest.raises(TypeError):
        should_hide_notification(True, "15")


# -------------------------------------------------
# E/21/253 - Emotion alert tests
# -------------------------------------------------

@pytest.mark.parametrize(
    ("emotion", "confidence", "expected"),
    [
        ("SAD", 79.99, False),
        ("SAD", 80, True),
        ("SAD", 80.01, True),
        ("ANGRY", 95, True),
        ("HAPPY", 95, False),
        ("CALM", 90, False),
        ("SAD", 0, False),
        ("SAD", 100, True),
        ("sad", 90, True),
    ],
)
def test_should_send_emotion_alert(emotion, confidence, expected):
    assert should_send_emotion_alert(emotion, confidence) is expected


@pytest.mark.parametrize("confidence", [-1, 101])
def test_emotion_alert_rejects_out_of_range_confidence(confidence):
    with pytest.raises(ValueError):
        should_send_emotion_alert("SAD", confidence)


def test_emotion_alert_rejects_empty_emotion():
    with pytest.raises(ValueError):
        should_send_emotion_alert("", 90)


def test_emotion_alert_rejects_invalid_emotion_type():
    with pytest.raises(TypeError):
        should_send_emotion_alert(None, 90)


def test_emotion_alert_rejects_invalid_confidence_type():
    with pytest.raises(TypeError):
        should_send_emotion_alert("SAD", "90")
