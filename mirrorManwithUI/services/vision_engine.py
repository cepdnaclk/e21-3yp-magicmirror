import cv2
import json
import time
import os
import sys
import threading
import requests
from datetime import datetime

try:
    from picamera2 import Picamera2
except ImportError:
    Picamera2 = None

from config.settings import BUCKET_NAME, COLLECTION_ID
from config.aws_config import get_rekognition_client, get_s3_client

# --- Module-level AWS Clients (None until first use) ---
rekognition = None
s3 = None


def _get_rekognition():
    """Return the Rekognition client, initialising it lazily on first call."""
    global rekognition
    if rekognition is None:
        rekognition = get_rekognition_client()
    return rekognition


def _get_s3():
    """Return the S3 client, initialising it lazily on first call."""
    global s3
    if s3 is None:
        s3 = get_s3_client()
    return s3
def check_is_present_api():
    """Query local FastAPI presence status."""
    try:
        response = requests.get("http://127.0.0.1:8000/api/presence/status", timeout=1)
        if response.status_code == 200:
            return response.json().get("is_present", False)
    except Exception:
        pass
    return False  # default to False (absent) if API is unreachable


def get_family_member_owners(detected_person):
    """Query DynamoDB to find all owners who have this detected_person in their FamilyMember list."""
    import boto3
    from config.settings import AWS_REGION

    clean_detected = detected_person.replace('_Owner_Self', '').strip().lower()

    # Get credentials/config values
    aws_keys = {
        'aws_access_key_id': os.getenv("AWS_ACCESS_KEY_ID") or None,
        'aws_secret_access_key': os.getenv("AWS_SECRET_ACCESS_KEY") or None,
        'region_name': AWS_REGION or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
    }

    owners = set()
    try:
        # Initialize client with available keys
        dynamodb = boto3.client('dynamodb', **{k: v for k, v in aws_keys.items() if v is not None})

        # 1. Dynamically locate the FamilyMember table
        table_name = None
        tables = dynamodb.list_tables().get("TableNames", [])
        for t in tables:
            if t.startswith("FamilyMember-"):
                table_name = t
                break

        if not table_name:
            print("⚠️  DynamoDB FamilyMember table not found in AWS account.", flush=True)
            return []

        # 2. Scan items and filter for matches
        paginator = dynamodb.get_paginator('scan')
        for page in paginator.paginate(TableName=table_name):
            for item in page.get('Items', []):
                db_name = item.get('name', {}).get('S', '').strip().lower()
                db_owner = item.get('owner', {}).get('S', '').strip()

                if not db_owner:
                    continue

                # Check if detected person matches the DB family member name
                # E.g. db_name is "sithu@gmail.com" -> clean_db_name is "sithu"
                # detected_person is "sithu_Owner_Self" or "sithu" -> clean_detected is "sithu"
                clean_db_name = db_name.split('@')[0].replace('.', '_').replace('-', '_').strip().lower()
                clean_detected_norm = clean_detected.replace('.', '_').replace('-', '_').strip().lower()

                if clean_db_name == clean_detected_norm or clean_detected_norm in clean_db_name or clean_db_name in clean_detected_norm:
                    # Resolve clean owner prefix from imagePaths to match mobile app folder naming (e.g., 'slhelix300')
                    resolved_owner = None
                    image_paths = item.get('imagePaths', {}).get('L', [])
                    if image_paths:
                        first_path = image_paths[0].get('S', '')
                        if first_path:
                            filename = os.path.basename(first_path)
                            # Format: {mainUserEmail}_{cleanName}_{angle}.jpg
                            parts = filename.split('_')
                            if parts:
                                resolved_owner = parts[0].strip().lower()
                    
                    if not resolved_owner:
                        resolved_owner = db_owner
                        
                    owners.add(resolved_owner)

    except Exception as e:
        print(f"⚠️  DynamoDB query failed: {e}", flush=True)

    return list(owners)


def send_alert_to_app(person_name, emotion):
    """Uploads an Alert JSON to the S3 bucket inside each matching family member's folder."""
    s3_client = _get_s3()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Find all owners who registered this person as a family member
    owners = get_family_member_owners(person_name)

    # 2. Fallback to writing directly to the person's own folder if no owners found
    if not owners:
        owners = [person_name]

    for owner in owners:
        # Strip any ownership/email suffix to get a clean S3 user ID prefix
        clean_user_id = owner.split('@')[0].replace('_Owner_Self', '').strip().lower()

        alert_data = {
            "user_id": clean_user_id,
            "emotion": emotion,
            "time": timestamp,
            "message": f"Attention! {person_name.replace('_Owner_Self', '')} is currently feeling {emotion}.",
            "status": "unread"
        }

        # Targeted upload for each owner
        file_name = f"public/alerts/{clean_user_id}/alert_{timestamp}.json"

        try:
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=file_name,
                Body=json.dumps(alert_data),
                ContentType='application/json'
            )
            print(f"📡 [ALERT SENT] S3 Path: {file_name}", flush=True)
        except Exception as e:
            print(f"❌ [ALERT ERROR] S3 Upload failed to {file_name}: {e}", flush=True)


def process_image(img_bytes):
    """Handles blocking AWS Rekognition calls in a background thread."""
    rek = _get_rekognition()
    try:
        # 1. Detect face emotions
        face_detail = rek.detect_faces(
            Image={'Bytes': img_bytes},
            Attributes=['EMOTIONS']
        )

        if face_detail['FaceDetails']:
            emotions = face_detail['FaceDetails'][0]['Emotions']
            primary_emotion_data = max(emotions, key=lambda x: x['Confidence'])
            primary_emotion = primary_emotion_data['Type']
            confidence = primary_emotion_data['Confidence']

            # 2. Identify the person via face search
            search_res = rek.search_faces_by_image(
                CollectionId=COLLECTION_ID,
                Image={'Bytes': img_bytes},
                MaxFaces=1,
                FaceMatchThreshold=85
            )

            if search_res['FaceMatches']:
                name = search_res['FaceMatches'][0]['Face']['ExternalImageId']
                print(f"👤 [DETECTED] {name} | 🎭 [EMOTION] {primary_emotion} ({confidence:.1f}%)", flush=True)

                # 3. Alert only on negative emotions
                if primary_emotion in ["SAD", "ANGRY", "FEAR"]:
                    send_alert_to_app(name, primary_emotion)
            else:
                print(f"❓ [UNKNOWN] Face found but not identified | Emotion: {primary_emotion}", flush=True)

        else:
            print("--- Scanning... (No faces found) ---", flush=True)

    except Exception as e:
        print(f"⚠️ [ENGINE ERROR] Rekognition error: {e}", flush=True)


def _run_with_picamera():
    """Camera loop using Picamera2 (Raspberry Pi)."""
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(
        main={"size": (640, 480), "format": "RGB888"}
    )
    picam2.configure(config)
    picam2.start()
    print("👁️ ReflectStudio Vision Engine LIVE (PiCam2 Mode)...", flush=True)

    last_process_time = time.time()
    try:
        while True:
            if not check_is_present_api():
                time.sleep(2)
                continue
            frame = picam2.capture_array()
            current_time = time.time()
            if current_time - last_process_time >= 10:
                last_process_time = current_time
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                _, buffer = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
                img_bytes = buffer.tobytes()
                threading.Thread(target=process_image, args=(img_bytes,), daemon=True).start()
    except KeyboardInterrupt:
        print("\n--- Shutting down ReflectStudio (PiCam2) ---", flush=True)
    finally:
        picam2.stop()


def _run_with_opencv():
    """Camera loop using OpenCV VideoCapture (PC / USB webcam fallback)."""
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 10)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        return False

    print("👁️ ReflectStudio Vision Engine LIVE (OpenCV / Webcam Mode)...", flush=True)

    last_process_time = time.time()
    try:
        while True:
            if not check_is_present_api():
                time.sleep(2)
                continue
            ret, frame = cap.read()
            if not ret:
                break
            current_time = time.time()
            if current_time - last_process_time >= 10:
                last_process_time = current_time
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                img_bytes = buffer.tobytes()
                threading.Thread(target=process_image, args=(img_bytes,), daemon=True).start()
    except KeyboardInterrupt:
        print("\n--- Shutting down ReflectStudio (OpenCV) ---", flush=True)
    finally:
        cap.release()

    return True


def _run_mock():
    """Mock mode — no camera available. Idle and keep the process alive."""
    print("⚠️  ReflectStudio Vision Engine (MOCK MODE — No Camera)...", flush=True)
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n--- Shutting down ReflectStudio (Mock) ---", flush=True)


def run_vision():
    """Main entry-point. Tries Picamera2 → OpenCV → Mock in priority order."""
    print("--- Starting ReflectStudio Vision Engine ---", flush=True)

    if Picamera2 is not None:
        try:
            _run_with_picamera()
            sys.exit(0)
        except Exception as e:
            print(f"⚠️  Picamera2 failed ({e}). Falling back to OpenCV...", flush=True)

    try:
        if _run_with_opencv():
            sys.exit(0)
        print("⚠️  No camera found via OpenCV. Running in mock mode.", flush=True)
    except Exception as e:
        print(f"⚠️  OpenCV failed ({e}). Running in mock mode.", flush=True)

    _run_mock()
    sys.exit(0)


if __name__ == "__main__":
    run_vision()