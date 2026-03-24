from app.services.storage_service import (  # type: ignore  # noqa: F401
    upload_document,
    generate_presigned_url,
    download_file,
)

# Module-level aliases for backward compatibility
storage_service = type("StorageService", (), {
    "upload_document": staticmethod(upload_document),
    "generate_presigned_url": staticmethod(generate_presigned_url),
    "download_file": staticmethod(download_file),
})()

from app.services.ocr_service import ocr_service  # type: ignore  # noqa: F401, E402
from app.services.pii_service import PIIRedactor  # type: ignore  # noqa: F401, E402
