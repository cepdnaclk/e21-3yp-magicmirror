import cv2
import boto3
import json
import time
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from picamera2 import Picamera2

# Load environment variables (Make sure your .env file is correct)
load_dotenv()

# --- AWS CONFIG ---
# If you don't use .env, you can replace these with your actual keys like before
REGION = os.getenv("AWS_REGION")
BUCKET_NAME = os.getenv("BUCKET_NAME")
COLLECTION_ID = os.getenv("COLLECTION_ID")
# Initialize AWS Clients
print("--- Initializing AWS Services ---", flush=True)
rekognition = boto3.client("rekognition", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)
print("? AWS Services Connected.", flush=True)

def send_alert_to_app(person_name, emotion):
    """Uploads an alert JSON to S3 for the mobile app"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    alert_data = {
        "user_id": person_name,
        "emotion": emotion,
        "time": timestamp,
        "message": f"Attention! {person_name} is currently feeling {emotion}.",
        "status": "unread"
    }

    file_name = f"public/alerts/alert_{person_name}_{timestamp}.json"

    try:
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=file_name,
            Body=json.dumps(alert_data),
            ContentType="application/json"
        )
        print(f"?? [ALERT SENT] S3 Path: {file_name}", flush=True)
    except Exception as e:
        print(f"? [ALERT ERROR] S3 Upload failed: {e}", flush=True)

def run_vision():
    # Initialize PiCamera2
    print("--- Starting PiCamera2 Hardware ---", flush=True)
    picam2 = Picamera2()

    # Optimized configuration for fast face detection
    config = picam2.create_preview_configuration(
        main={"size": (640, 480), "format": "RGB888"}
    )
    picam2.configure(config)
    picam2.start()

    print("??? ReflectStudio Vision Engine LIVE (PiCam2 Mode)...", flush=True)

    try:
        while True:
            # Capture the freshest frame directly as an array
            frame = picam2.capture_array()

            # Picamera2 gives RGB, OpenCV needs BGR for encoding
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # Encode to JPG for Rekognition
            success, buffer = cv2.imencode(".jpg", frame_bgr)
            if not success:
                print("?? [FRAME ERROR] Failed to encode frame. Retrying...", flush=True)
                continue

            img_bytes = buffer.tobytes()

            try:
                # 1. Detect Emotions
                face_detail = rekognition.detect_faces(
                    Image={"Bytes": img_bytes},
                    Attributes=["EMOTIONS"]
                )

                if face_detail["FaceDetails"]:
                    # Get the most confident emotion
                    emotions = face_detail["FaceDetails"][0]["Emotions"]
                    primary_emotion_data = max(emotions, key=lambda x: x["Confidence"])
                    primary_emotion = primary_emotion_data["Type"]
                    confidence = primary_emotion_data["Confidence"]

                    # 2. Identify Person
                    search_res = rekognition.search_faces_by_image(
                        CollectionId=COLLECTION_ID,
                        Image={"Bytes": img_bytes},
                        MaxFaces=1,
                        FaceMatchThreshold=85
                    )

                    if search_res["FaceMatches"]:
                        name = search_res["FaceMatches"][0]["Face"]["ExternalImageId"]
                        print(f"?? [DETECTED] {name} | ?? [EMOTION] {primary_emotion} ({confidence:.1f}%)", flush=True)

                        # 3. Alert Logic (Only negative emotions)
                        if primary_emotion in ["SAD", "ANGRY", "FEAR"]:
                            send_alert_to_app(name, primary_emotion)
                    else:
                        print(f"? [UNKNOWN] Face found but not identified | Emotion: {primary_emotion}", flush=True)

                else:
                    print("--- Scanning... (No faces found) ---", flush=True)

            except Exception as e:
                print(f"?? [ENGINE ERROR] Rekognition error: {e}", flush=True)

            # Wait 10 seconds to save costs.
            # Note: If accuracy is still low, try reducing this to 5 seconds.
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n--- Shutting down ReflectStudio ---", flush=True)
    finally:
        picam2.stop()
        sys.exit()

if __name__ == "__main__":
    run_vision()

