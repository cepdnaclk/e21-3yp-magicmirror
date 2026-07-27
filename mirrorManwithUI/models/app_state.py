# ================= SHARED APPLICATION STATE =================
# Shared UI data (moved from main2.py globals)

notifications = []

# Reminders are now populated in real-time from DynamoDB via s3_watcher.
# This list starts empty; the mirror UI is updated every 60 s automatically.
priority_schedule = []

# Presence State
is_present = False
