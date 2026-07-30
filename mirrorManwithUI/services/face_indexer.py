import boto3
import os
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
REGION = os.getenv('AWS_REGION') or os.getenv('AWS_DEFAULT_REGION')
BUCKET = os.getenv('BUCKET_NAME')
COLLECTION_ID = os.getenv('COLLECTION_ID')

# --- Lazy AWS Clients ---
# Kept as module-level names so test patches (patch("services.face_indexer.rekognition"))
# continue to work. They are populated on first call to dynamic_indexing().
rekognition = None
s3 = None


def _ensure_clients():
    """Initialise AWS clients on first call (lazy) so importing this module never hangs."""
    global rekognition, s3
    if rekognition is None:
        rekognition = boto3.client(
            'rekognition',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=REGION
        )
    if s3 is None:
        s3 = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=REGION
        )


def dynamic_indexing():
    """Create/update the Rekognition collection from images uploaded to S3."""
    _ensure_clients()

    try:
        rekognition.create_collection(CollectionId=COLLECTION_ID)
        print(f"[CREATED] Collection '{COLLECTION_ID}' successfully created.")
    except rekognition.exceptions.ResourceAlreadyExistsException:
        print(f"[INFO] Collection '{COLLECTION_ID}' already exists.")

    print(f"[S3] Checking S3 Bucket: {BUCKET}")

    # Images are uploaded by the mobile app to this prefix
    PREFIX = "public/face_entries/"
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX)

    if 'Contents' not in response:
        print(f"[ERROR] No images found in {PREFIX} folder of the bucket.")
        return

    for obj in response['Contents']:
        full_path = obj['Key']  # e.g. public/face_entries/thenuka_front.jpg

        # Skip the folder entry itself
        if full_path == PREFIX:
            continue

        if full_path.lower().endswith(('.jpg', '.jpeg', '.png')):

            # 1. Extract only the filename (thenuka_front.jpg)
            file_name_only = full_path.replace(PREFIX, "")

            # 2. Remove angle suffix (_front / _left / _right) to get the clean ID
            if '_' in file_name_only:
                person_id = file_name_only.rsplit('_', 1)[0]

                # AWS rules: no slashes in ExternalImageId
                person_id = person_id.replace('/', '_')

                print(f"[INDEXING] {file_name_only} (ID: {person_id})")

                try:
                    rekognition.index_faces(
                        CollectionId=COLLECTION_ID,
                        Image={'S3Object': {'Bucket': BUCKET, 'Name': full_path}},
                        ExternalImageId=person_id,
                        DetectionAttributes=['ALL']
                    )
                    print("  --> [SUCCESS]")
                except Exception as e:
                    print(f"  --> [ERROR] {e}")


if __name__ == "__main__":
    dynamic_indexing()