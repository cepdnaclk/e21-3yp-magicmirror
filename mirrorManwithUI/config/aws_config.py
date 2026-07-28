import boto3
from botocore.config import Config
from config.settings import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
)

# Short timeout configuration to prevent hanging on slow network
timeout_config = Config(
    connect_timeout=2.0,
    read_timeout=2.0,
    retries={'max_attempts': 1}
)

def get_s3_client():
    """Returns a configured boto3 S3 client."""
    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
        config=timeout_config,
    )


def get_rekognition_client():
    """Returns a configured boto3 Rekognition client."""
    return boto3.client(
        'rekognition',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
        config=timeout_config,
    )
