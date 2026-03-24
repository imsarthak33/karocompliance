import os
import boto3  # type: ignore
from botocore.exceptions import ClientError  # type: ignore
from google.cloud import storage  # type: ignore
from pathlib import Path
from app.config import settings  # type: ignore

# Mode Selection: Use S3, GCS, or Local
STORAGE_BACKEND = settings.STORAGE_BACKEND
LOCAL_STORAGE_PATH = os.getenv("LOCAL_STORAGE_PATH", "./storage")

# Initialize Clients based on backend
s3_client = None
gcs_client = None

if STORAGE_BACKEND == "s3":
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION
    )
elif STORAGE_BACKEND == "gcs":
    # Google Cloud automatically finds credentials if running on GCP
    gcs_client = storage.Client()
elif STORAGE_BACKEND == "local":
    Path(LOCAL_STORAGE_PATH).mkdir(parents=True, exist_ok=True)

async def upload_document(file_bytes: bytes, file_name: str, folder: str = "documents") -> str:
    """Uploads a file to the configured storage backend."""
    storage_key = f"{folder}/{file_name}"
    
    if STORAGE_BACKEND == "local":
        local_path = Path(LOCAL_STORAGE_PATH) / storage_key
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(file_bytes)
        return storage_key
        
    if STORAGE_BACKEND == "s3":
        try:
            s3_client.put_object(Bucket=settings.S3_BUCKET_NAME, Key=storage_key, Body=file_bytes)  # type: ignore
            return storage_key
        except ClientError as e:
            raise Exception(f"Failed to upload to S3: {str(e)}")
            
    if STORAGE_BACKEND == "gcs":
        try:
            bucket = gcs_client.bucket(settings.GCS_BUCKET_NAME)  # type: ignore
            blob = bucket.blob(storage_key)
            blob.upload_from_string(file_bytes)
            return storage_key
        except Exception as e:
            raise Exception(f"Failed to upload to GCS: {str(e)}")
            
    raise Exception(f"Invalid STORAGE_BACKEND: {STORAGE_BACKEND}")

def generate_presigned_url(storage_key: str, expires_in: int = 900) -> str:
    """Generates a temporary access URL (or file path)."""
    if STORAGE_BACKEND == "local":
        return str(Path(LOCAL_STORAGE_PATH).absolute() / storage_key)
        
    if STORAGE_BACKEND == "s3":
        try:
            return s3_client.generate_presigned_url(  # type: ignore
                'get_object',
                Params={'Bucket': settings.S3_BUCKET_NAME, 'Key': storage_key},
                ExpiresIn=expires_in
            )
        except ClientError as e:
            raise Exception(f"Failed to generate S3 URL: {str(e)}")
            
    if STORAGE_BACKEND == "gcs":
        try:
            bucket = gcs_client.bucket(settings.GCS_BUCKET_NAME)  # type: ignore
            blob = bucket.blob(storage_key)
            return blob.generate_signed_url(expiration=expires_in)
        except Exception as e:
            raise Exception(f"Failed to generate GCS URL: {str(e)}")
            
    raise Exception(f"Invalid STORAGE_BACKEND: {STORAGE_BACKEND}")

async def download_file(storage_key: str) -> bytes:
    """Downloads a file from the configured storage backend."""
    if STORAGE_BACKEND == "local":
        local_path = Path(LOCAL_STORAGE_PATH) / storage_key
        with open(local_path, "rb") as f:
            return f.read()
            
    if STORAGE_BACKEND == "s3":
        try:
            response = s3_client.get_object(Bucket=settings.S3_BUCKET_NAME, Key=storage_key)  # type: ignore
            return response['Body'].read()
        except ClientError as e:
            raise Exception(f"Failed to download from S3: {str(e)}")
            
    if STORAGE_BACKEND == "gcs":
        try:
            bucket = gcs_client.bucket(settings.GCS_BUCKET_NAME)  # type: ignore
            blob = bucket.blob(storage_key)
            return blob.download_as_bytes()
        except Exception as e:
            raise Exception(f"Failed to download from GCS: {str(e)}")
            
    raise Exception(f"Invalid STORAGE_BACKEND: {STORAGE_BACKEND}")
