import boto3
import os
from dotenv import load_dotenv

load_dotenv()

# --- YOUR AWS CREDENTIALS ---
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
REGION = os.getenv('AWS_DEFAULT_REGION')
BUCKET = os.getenv('BUCKET_NAME')
COLLECTION_ID = os.getenv('COLLECTION_ID')

# AWS Connection
rekognition = boto3.client('rekognition', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=REGION)
s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=REGION)

def dynamic_indexing():
    try:
        rekognition.create_collection(CollectionId=COLLECTION_ID)
        print(f"✅ Collection '{COLLECTION_ID}' successfully created.")
    except rekognition.exceptions.ResourceAlreadyExistsException:
        print(f"ℹ️ Collection '{COLLECTION_ID}' already exists.")

    print(f"📂 Checking S3 Bucket: {BUCKET}")
    
    # Provide the correct path where images are located
    PREFIX = "public/face_entries/"
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX)

    if 'Contents' not in response:
        print(f"❌ No images found in {PREFIX} folder of the bucket.")
        return

    for obj in response['Contents']:
        full_path = obj['Key'] # e.g., public/face_entries/thenuka_front.jpg
        
        # Check if it's a file, not the folder itself
        if full_path == PREFIX:
            continue

        if full_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            
            # 1. Extract only the file name (thenuka_front.jpg)
            file_name_only = full_path.replace(PREFIX, "")
            
            # 2. Remove '_front.jpg' to get the clean ID
            if '_' in file_name_only:
                person_id = file_name_only.rsplit('_', 1)[0]
                
                # AWS rules: remove / and provide a clean ID
                person_id = person_id.replace('/', '_')

                print(f"🔍 Indexing: {file_name_only} (ID: {person_id})")

                try:
                    # Provide the Bucket and the full path here
                    rekognition.index_faces(
                        CollectionId=COLLECTION_ID,
                        Image={'S3Object': {'Bucket': BUCKET, 'Name': full_path}},
                        ExternalImageId=person_id,
                        DetectionAttributes=['ALL']
                    )
                    print(f"  ✅ Success!")
                except Exception as e:
                    print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    dynamic_indexing()