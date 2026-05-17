import asyncio
import json

from config.settings import BUCKET_NAME
from config.aws_config import get_s3_client
from controllers.websocket_manager import manager


# ================= BACKGROUND AWS WATCHER =================
# ================= BACKGROUND AWS WATCHER =================
async def check_s3_inbox():
    """App ????? ??? notifications ?? reminders ??? ???"""
    s3 = get_s3_client()
    print("?? Connected to AWS. Watching for App messages...")
    while True:
        try:
            # 1. ?????? (Notifications) ??????? ?????
            notif_res = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix="public/notifications/")
            if 'Contents' in notif_res:
                for item in notif_res['Contents']:
                    file_key = item['Key']
                    if not file_key.endswith('.txt'): continue

                    obj = s3.get_object(Bucket=BUCKET_NAME, Key=file_key)
                    msg = obj['Body'].read().decode('utf-8')

                    print(f"?? APP NOTIFICATION: {msg}")
                    # UI ??? ?????
                    await manager.broadcast(json.dumps({"type": "notification", "message": msg}))
                    # ?????? ?? ????? ?????
                    s3.delete_object(Bucket=BUCKET_NAME, Key=file_key)

            # 2. ???? ?????? (Reminders) ??????? ?????
            rem_res = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix="public/reminders/")
            if 'Contents' in rem_res:
                for item in rem_res['Contents']:
                    file_key = item['Key']
                    if not file_key.endswith('.txt'): continue

                    obj = s3.get_object(Bucket=BUCKET_NAME, Key=file_key)
                    msg = obj['Body'].read().decode('utf-8')

                    print(f"??? NEW REMINDER: {msg}")
                    await manager.broadcast(json.dumps({"type": "reminder", "message": msg}))
                    s3.delete_object(Bucket=BUCKET_NAME, Key=file_key)

        except Exception as e:
            print(f"?? S3 Error: {e}")

        await asyncio.sleep(5) # ????? 5?? ?????? ?????
