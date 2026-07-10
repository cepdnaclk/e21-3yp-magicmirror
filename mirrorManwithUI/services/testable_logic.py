"""
testable_logic.py
-----------------
Pure business-logic helpers extracted from Reflect Studio services.
No hardware, AWS, GPIO, or audio dependencies — safe to unit-test anywhere.

Functions
---------
classify_voice_command  – maps a raw voice string to an action token
validate_reminder       – validates a reminder message + scheduled time
should_hide_notification – decides when a 15-second notification should hide
should_send_emotion_alert – decides whether a detected emotion warrants an alert
"""

from __future__ import annotations

from datetime import datetime

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Emotions treated as negative (must match AWS Rekognition labels, upper-case)
NEGATIVE_EMOTIONS: frozenset[str] = frozenset({"SAD", "ANGRY", "FEAR", "DISGUSTED", "CONFUSED"})

# Minimum confidence (%) for an emotion to trigger an alert
EMOTION_CONFIDENCE_THRESHOLD: float = 80.0

# How long (seconds) a notification stays on screen while someone is present
NOTIFICATION_DISPLAY_SECONDS: float = 15.0

# Maximum allowed reminder message length (characters)
MAX_REMINDER_LENGTH: int = 200


# ---------------------------------------------------------------------------
# 1. Voice-command classifier  (E/21/287 - Perera G.S.H)
# ---------------------------------------------------------------------------

def classify_voice_command(text: str) -> str:
    """
    Classify a raw voice-command string into a structured action token.

    Parameters
    ----------
    text : str
        Raw transcribed voice input (may have surrounding whitespace).

    Returns
    -------
    str
        One of:
        ``ACTIVATE_MIRROR_MAN`` | ``DEACTIVATE_MIRROR_MAN`` |
        ``PLAY_MUSIC`` | ``PAUSE_MUSIC`` | ``RESUME_MUSIC`` |
        ``STOP_MUSIC`` | ``UNKNOWN``

    Raises
    ------
    TypeError
        If *text* is not a ``str``.
    ValueError
        If *text* is empty (after stripping), or if the play command
        contains no song name.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")

    stripped = text.strip()

    if not stripped:
        raise ValueError("Voice command must not be empty")

    lower = stripped.lower()

    # --- Mirror Man activation / deactivation ---
    if lower == "hello mirror":
        return "ACTIVATE_MIRROR_MAN"

    if lower in ("good bye", "goodbye"):
        return "DEACTIVATE_MIRROR_MAN"

    # --- Music controls (exact or prefix match) ---
    if lower == "pause music":
        return "PAUSE_MUSIC"

    if lower == "resume music":
        return "RESUME_MUSIC"

    if lower == "stop music":
        return "STOP_MUSIC"

    # --- Play <song name> ---
    play_prefixes = (
        "play me some ", "play me a ", "play me ",
        "play some ", "play a ", "play the ", "play ",
    )
    for prefix in play_prefixes:
        if lower.startswith(prefix):
            song = stripped[len(prefix):].strip()
            if not song:
                raise ValueError("Play command must include a song name")
            return "PLAY_MUSIC"

    # "play" with nothing after it (e.g. "Play " stripped to "play")
    if lower == "play":
        raise ValueError("Play command must include a song name")

    return "UNKNOWN"


# ---------------------------------------------------------------------------
# 2. Reminder validator  (E/21/229 - Kurera P.A.T)
# ---------------------------------------------------------------------------

def validate_reminder(
    message: str,
    scheduled_time: datetime,
    current_time: datetime,
) -> bool:
    """
    Validate a reminder before it is stored / sent to the mirror.

    Parameters
    ----------
    message : str
        The reminder text to display.
    scheduled_time : datetime
        When the reminder should appear.
    current_time : datetime
        The reference "now" (injected so the function is testable).

    Returns
    -------
    bool
        ``True`` when the reminder is valid.

    Raises
    ------
    TypeError
        If *message* is not a ``str``, or if either datetime argument is
        not a ``datetime`` instance.
    ValueError
        If *message* is blank or exceeds ``MAX_REMINDER_LENGTH``,
        or if *scheduled_time* is not strictly in the future.
    """
    if not isinstance(message, str):
        raise TypeError(f"message must be str, got {type(message).__name__}")

    if not isinstance(scheduled_time, datetime) or not isinstance(current_time, datetime):
        raise TypeError("scheduled_time and current_time must be datetime objects")

    if not message.strip():
        raise ValueError("Reminder message must not be blank")

    if len(message) > MAX_REMINDER_LENGTH:
        raise ValueError(
            f"Reminder message exceeds {MAX_REMINDER_LENGTH} characters "
            f"(got {len(message)})"
        )

    if scheduled_time <= current_time:
        raise ValueError("scheduled_time must be strictly in the future")

    return True


# ---------------------------------------------------------------------------
# 3. Notification visibility  (E/21/055 - Bandara K.N.K.L.N)
# ---------------------------------------------------------------------------

def should_hide_notification(presence: bool, elapsed_seconds: float) -> bool:
    """
    Decide whether the on-screen notification banner should be hidden.

    The notification is hidden when:
    * A person is still present **and** the display window has expired
      (``elapsed_seconds >= NOTIFICATION_DISPLAY_SECONDS``).

    If no one is present the notification is never shown, so hiding is
    meaningless — return ``False``.

    Parameters
    ----------
    presence : bool
        ``True`` if a person is currently detected in front of the mirror.
    elapsed_seconds : float
        Seconds since the notification was first displayed.

    Returns
    -------
    bool
        ``True`` → hide the notification now.

    Raises
    ------
    TypeError
        If *presence* is not ``bool`` or *elapsed_seconds* is not numeric.
    ValueError
        If *elapsed_seconds* is negative.
    """
    if not isinstance(presence, bool):
        raise TypeError(
            f"presence must be bool, got {type(presence).__name__}"
        )
    if not isinstance(elapsed_seconds, (int, float)):
        raise TypeError(
            f"elapsed_seconds must be a number, got {type(elapsed_seconds).__name__}"
        )
    if elapsed_seconds < 0:
        raise ValueError("elapsed_seconds must not be negative")

    return presence and elapsed_seconds >= NOTIFICATION_DISPLAY_SECONDS


# ---------------------------------------------------------------------------
# 4. Emotion-alert filter  (E/21/253 - Manabandu J.P.G.T.R)
# ---------------------------------------------------------------------------

def should_send_emotion_alert(emotion: str, confidence: float) -> bool:
    """
    Decide whether an AWS Rekognition emotion result should trigger an alert
    to the caregiver's mobile app.

    An alert is sent when **both** conditions hold:
    1. The detected emotion is one of the ``NEGATIVE_EMOTIONS``.
    2. Rekognition's confidence is at or above ``EMOTION_CONFIDENCE_THRESHOLD``.

    Parameters
    ----------
    emotion : str
        Emotion label returned by AWS Rekognition (e.g. ``"SAD"``).
        Case-insensitive.
    confidence : float
        Rekognition's confidence percentage (0–100 inclusive).

    Returns
    -------
    bool
        ``True`` → send an alert to the caregiver.

    Raises
    ------
    TypeError
        If *emotion* is not ``str`` or *confidence* is not numeric.
    ValueError
        If *emotion* is empty, or *confidence* is outside ``[0, 100]``.
    """
    if not isinstance(emotion, str):
        raise TypeError(
            f"emotion must be str, got {type(emotion).__name__}"
        )
    if not isinstance(confidence, (int, float)):
        raise TypeError(
            f"confidence must be a number, got {type(confidence).__name__}"
        )

    if not emotion.strip():
        raise ValueError("emotion must not be empty")

    if not (0 <= confidence <= 100):
        raise ValueError(
            f"confidence must be between 0 and 100 (got {confidence})"
        )

    return (
        emotion.upper() in NEGATIVE_EMOTIONS
        and confidence >= EMOTION_CONFIDENCE_THRESHOLD
    )
