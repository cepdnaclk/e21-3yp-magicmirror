import cv2
import boto3
import json
import time
import os
import threading
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

# --- AWS CONFIG ---
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
REGION = os.getenv('AWS_DEFAULT_REGION')
BUCKET_NAME = os.getenv('BUCKET_NAME')
COLLECTION_ID = os.getenv('COLLECTION_ID')

# Clients
rekognition = boto3.client('rekognition', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=REGION)
s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=REGION)

def send_alert_to_app(person_name, emotion):
    """Uploads an Alert JSON to the S3 bucket"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Strip the owner suffix to match the mobile app's user ID folder
    clean_user_id = person_name.replace('_Owner_Self', '')
    
    alert_data = {
        "user_id": clean_user_id,
        "emotion": emotion,
        "time": timestamp,
        "message": f"Attention! {clean_user_id} is currently feeling {emotion}.",
        "status": "unread"
    }
    
    # Targeted Upload: Save the alert INSIDE the specific detected person's folder!
    file_name = f"public/alerts/{clean_user_id}/alert_{timestamp}.json"
    
    try:
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=file_name,
            Body=json.dumps(alert_data),
            ContentType='application/json'
        )
        print(f"📡 Sent Alert: {file_name}")
    except Exception as e:
        print(f"❌ Alert error: {e}")

def process_image(img_bytes):
    """Handles the blocking AWS Rekognition requests in a background thread."""
    try:
        # 1. Detect face and emotions in the image
        face_detail = rekognition.detect_faces(Image={'Bytes': img_bytes}, Attributes=['EMOTIONS'])
        
        if face_detail['FaceDetails']:
            emotion = max(face_detail['FaceDetails'][0]['Emotions'], key=lambda x: x['Confidence'])['Type']
            
            # 2. Identify the person
            search_res = rekognition.search_faces_by_image(
                CollectionId=COLLECTION_ID,
                Image={'Bytes': img_bytes},
                MaxFaces=1,
                FaceMatchThreshold=85
            )

            if search_res['FaceMatches']:
                name = search_res['FaceMatches'][0]['Face']['ExternalImageId']
                print(f"👤 Recognized {name} | 🎭 Emotion: {emotion}")

                # 3. Important: Send alert only if feeling sad, angry, or fearful
                if emotion in ['SAD', 'ANGRY', 'FEAR']:
                    send_alert_to_app(name, emotion)
            else:
                print(f"❓ Unrecognized face | 🎭 Emotion: {emotion}")

    except Exception as e:
        print(f"Error: {e}")

def run_vision():
    cap = cv2.VideoCapture(0)
    # Hardware level optimizations for Raspberry Pi
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 10)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Force camera buffer to 1 frame to reduce latency
    print("👁️ ReflectStudio Vision Engine Alert System is active...")

    last_process_time = time.time()

    while True:
        # Constantly read frames to keep the hardware buffer empty and prevent lag
        ret, frame = cap.read()
        if not ret: break

        current_time = time.time()
        
        # Only process AWS Rekognition once every 10 seconds
        if current_time - last_process_time >= 10:
            last_process_time = current_time
            
            # Directly encode the frame since we already set hardware resolution to 640x480
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            img_bytes = buffer.tobytes()

            # Run the heavy AWS API calls in a separate thread so camera keeps reading frames!
            threading.Thread(target=process_image, args=(img_bytes,), daemon=True).start()

if __name__ == "__main__":
    run_vision()