import os
import boto3  # type: ignore
from botocore.exceptions import ClientError  # type: ignore
from pathlib import Path

# Enforce strict 15-minute (900 seconds) expiration rule for signed URLs
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
LOCAL_STORAGE_PATH = os.getenv("LOCAL_STORAGE_PATH", "./storage")

# Mode Selection: Use S3 if keys are present, else fallback to Local
IS_LOCAL = not AWS_ACCESS_KEY_ID or os.getenv("STORAGE_BACKEND") == "local"

if not IS_LOCAL:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )
else:
    # Ensure local storage dir exists
    Path(LOCAL_STORAGE_PATH).mkdir(parents=True, exist_ok=True)

async def upload_document(file_bytes: bytes, file_name: str, folder: str = "documents") -> str:
    """Uploads a file to S3 (or Local) and returns the key/path."""
    s3_key = f"{folder}/{file_name}"
    
    if IS_LOCAL:
        local_path = Path(LOCAL_STORAGE_PATH) / s3_key
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(file_bytes)
        return s3_key
    
    try:
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=s3_key, Body=file_bytes)
        return s3_key
    except ClientError as e:
        raise Exception(f"Failed to upload to S3: {str(e)}")

def generate_presigned_url(s3_key: str, expires_in: int = 900) -> str:
    """Generates a strictly temporary access URL (or file path)."""
    if IS_LOCAL:
        # Return a absolute file path string for local testing
        return str(Path(LOCAL_STORAGE_PATH).absolute() / s3_key)
        
    try:
        return s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=expires_in
        )
    except ClientError as e:
        raise Exception(f"Failed to generate signed URL: {str(e)}")

async def download_file(s3_key: str) -> bytes:
    """Downloads a file from S3 (or Local) and returns its bytes."""
    if IS_LOCAL:
        local_path = Path(LOCAL_STORAGE_PATH) / s3_key
        with open(local_path, "rb") as f:
            return f.read()
            
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        return response['Body'].read()
    except ClientError as e:
        raise Exception(f"Failed to download from S3: {str(e)}")
