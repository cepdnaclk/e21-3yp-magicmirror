import asyncio
import json
import os
import boto3
from datetime import datetime

from config.settings import BUCKET_NAME
from config.aws_config import get_s3_client
from controllers.websocket_manager import manager


# ─────────────────────────────────────────────────
# DynamoDB helper — parse reminder date + time
# ─────────────────────────────────────────────────
def _parse_reminder_datetime(date_str: str, time_str: str):
    """Return a datetime from the app's stored date/time strings, or None if invalid.

    date_str format: "6/4/2025" (m/d/Y, no zero-padding) or "Today"
    time_str format: "2:30 PM"  (12-hour) or "Anytime"
    """
    try:
        if date_str.lower() == "today":
            date_part = datetime.now().date()
        else:
            date_part = datetime.strptime(date_str, "%m/%d/%Y").date()

        if time_str.lower() == "anytime":
            # Treat as end of that day so it shows all day
            return datetime.combine(date_part, datetime.max.time())
        else:
            time_part = datetime.strptime(time_str, "%I:%M %p").time()
            return datetime.combine(date_part, time_part)
    except Exception:
        return None


def get_upcoming_reminders():
    """Scan the DynamoDB Reminder table and return only future reminders."""
    try:
        dynamodb = boto3.client(
            "dynamodb",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "ap-southeast-1"),
        )

        # Dynamically find the Reminder table (Amplify names it Reminder-{hash}-dev)
        tables = dynamodb.list_tables().get("TableNames", [])
        table_name = next((t for t in tables if t.startswith("Reminder-")), None)
        if not table_name:
            print("⚠️  DynamoDB Reminder table not found.", flush=True)
            return []

        now = datetime.now()
        upcoming = []

        paginator = dynamodb.get_paginator("scan")
        for page in paginator.paginate(TableName=table_name):
            for item in page.get("Items", []):
                date_str  = item.get("date",   {}).get("S", "Today")
                time_str  = item.get("time",   {}).get("S", "Anytime")
                reason    = item.get("reason", {}).get("S", "")
                item_id   = item.get("id",     {}).get("S", "")

                scheduled_dt = _parse_reminder_datetime(date_str, time_str)
                if scheduled_dt and scheduled_dt >= now:
                    upcoming.append({
                        "id":           item_id,
                        "date":         date_str,
                        "time":         time_str,
                        "reason":       reason,
                        # JavaScript Date.now() epoch (ms) — used by UI to auto-prune
                        "expiry_epoch": int(scheduled_dt.timestamp() * 1000),
                    })

        # Sort soonest first
        upcoming.sort(key=lambda x: x["expiry_epoch"])
        return upcoming

    except Exception as e:
        print(f"⚠️  DynamoDB Reminder query failed: {e}", flush=True)
        return []


# ─────────────────────────────────────────────────
# Main polling loop
# ─────────────────────────────────────────────────
async def check_s3_inbox():
    """Poll S3 (instant messages) + DynamoDB (scheduled reminders) every 5 s.
    DynamoDB is re-queried every 60 s to avoid excess API calls."""
    s3 = get_s3_client()
    print("📡 Connected to AWS. Watching for App messages...", flush=True)

    db_poll_counter = 0       # query DynamoDB once every 12 × 5 s = 60 s
    DB_POLL_INTERVAL = 12

    poll_interval = 5
    while True:
        try:
            # ── 1. Instant notifications from caregiver ──────────────────
            notif_res = s3.list_objects_v2(
                Bucket=BUCKET_NAME, Prefix="public/notifications/"
            )
            if "Contents" in notif_res:
                for item in notif_res["Contents"]:
                    file_key = item["Key"]
                    if not file_key.endswith(".txt"):
                        continue
                    obj = s3.get_object(Bucket=BUCKET_NAME, Key=file_key)
                    msg = obj["Body"].read().decode("utf-8")
                    print(f"📩 APP NOTIFICATION: {msg}", flush=True)
                    await manager.broadcast(
                        json.dumps({"type": "notification", "message": msg})
                    )
                    s3.delete_object(Bucket=BUCKET_NAME, Key=file_key)

            # ── 2. Legacy S3 reminder triggers (instant, one-shot) ────────
            rem_res = s3.list_objects_v2(
                Bucket=BUCKET_NAME, Prefix="public/reminders/"
            )
            if "Contents" in rem_res:
                for item in rem_res["Contents"]:
                    file_key = item["Key"]
                    if not file_key.endswith(".txt"):
                        continue
                    obj = s3.get_object(Bucket=BUCKET_NAME, Key=file_key)
                    msg = obj["Body"].read().decode("utf-8")
                    print(f"⏰ NEW REMINDER (S3): {msg}", flush=True)
                    await manager.broadcast(
                        json.dumps({"type": "reminder", "message": msg})
                    )
                    s3.delete_object(Bucket=BUCKET_NAME, Key=file_key)

            # ── 3. DynamoDB scheduled reminders (every 60 s) ─────────────
            db_poll_counter += 1
            if db_poll_counter >= DB_POLL_INTERVAL:
                db_poll_counter = 0
                upcoming = get_upcoming_reminders()
                print(
                    f"📅 Broadcasting {len(upcoming)} upcoming reminder(s).",
                    flush=True,
                )
                await manager.broadcast(
                    json.dumps({"type": "reminder_list", "items": upcoming})
                )
            poll_interval = 5

        except Exception as e:
            print(f"⚠️  S3 Watcher Error: {e}", flush=True)
            poll_interval = 30

        await asyncio.sleep(poll_interval)
