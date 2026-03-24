import os
from google.cloud import storage  # type: ignore
print("DEBUG: Importing pathlib...")
from pathlib import Path
print("DEBUG: Importing app.config...")
from app.config import settings  # type: ignore

# Mode Selection: Use GCS or Local
print(f"DEBUG: STORAGE_BACKEND from settings: {settings.STORAGE_BACKEND}")
STORAGE_BACKEND = settings.STORAGE_BACKEND
LOCAL_STORAGE_PATH = os.getenv("LOCAL_STORAGE_PATH", "./storage")

# Initialize Client based on backend
gcs_client = None

if STORAGE_BACKEND == "gcs":
    # Google Cloud automatically finds credentials if running on GCP
    gcs_client = storage.Client()
elif STORAGE_BACKEND == "local":
    Path(LOCAL_STORAGE_PATH).mkdir(parents=True, exist_ok=True)

async def upload_document(file_bytes: bytes, file_name: str, folder: str = "documents") -> str:
    """Uploads a file to the configured storage backend (GCS or Local)."""
    storage_key = f"{folder}/{file_name}"
    
    if STORAGE_BACKEND == "local":
        local_path = Path(LOCAL_STORAGE_PATH) / storage_key
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(file_bytes)
        return storage_key
        
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
        
    if STORAGE_BACKEND == "gcs":
        try:
            bucket = gcs_client.bucket(settings.GCS_BUCKET_NAME)  # type: ignore
            blob = bucket.blob(storage_key)
            return blob.generate_signed_url(expiration=expires_in)
        except Exception as e:
            raise Exception(f"Failed to generate GCS URL: {str(e)}")
            
    raise Exception(f"Invalid STORAGE_BACKEND: {STORAGE_BACKEND}")

async def download_file(storage_key: str) -> bytes:
    """Downloads a file from the configured storage backend (GCS or Local)."""
    if STORAGE_BACKEND == "local":
        local_path = Path(LOCAL_STORAGE_PATH) / storage_key
        with open(local_path, "rb") as f:
            return f.read()
            
    if STORAGE_BACKEND == "gcs":
        try:
            bucket = gcs_client.bucket(settings.GCS_BUCKET_NAME)  # type: ignore
            blob = bucket.blob(storage_key)
            return blob.download_as_bytes()
        except Exception as e:
            raise Exception(f"Failed to download from GCS: {str(e)}")
            
    raise Exception(f"Invalid STORAGE_BACKEND: {STORAGE_BACKEND}")

storage_service = {
    "upload_document": upload_document,
    "generate_presigned_url": generate_presigned_url,
    "download_file": download_file
}
