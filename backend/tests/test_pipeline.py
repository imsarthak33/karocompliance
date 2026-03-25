import pytest
import hmac
import hashlib
import json
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.main import app
from app.config import settings
from app.database import get_db

def override_get_db():
    mock_db = MagicMock()
    mock_ca_firm = MagicMock()
    mock_ca_firm.id = "fake_ca_id"
    mock_client = MagicMock()
    mock_client.id = "fake_client_id"
    
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        mock_ca_firm,
        mock_client,
        None,
    ]
    yield mock_db

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def generate_wa_signature(payload_bytes: bytes, secret: str) -> str:
    """Generates the X-Hub-Signature-256 header."""
    signature = hmac.new(secret.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()
    return f"sha256={signature}"

@pytest.fixture
def mock_whatsapp_payload():
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "12345",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "1234567890", "phone_number_id": "9876543210"},
                    "contacts": [{"profile": {"name": "Test Client"}, "wa_id": "919876543210"}],
                    "messages": [{
                        "from": "919876543210",
                        "id": "wamid.HBgLOTE5ODc2NTQzMjEw",
                        "timestamp": "1690885145",
                        "type": "image",
                        "image": {"mime_type": "image/jpeg", "sha256": "hash", "id": "media_123"}
                    }]
                },
                "field": "messages"
            }]
        }]
    }

@patch('app.routers.webhooks._get_redis')
@patch('app.routers.webhooks.process_incoming_document.delay')
@patch('app.routers.webhooks.upload_document')
@patch('app.routers.webhooks.download_media')
def test_whatsapp_webhook_pipeline(mock_download, mock_upload, mock_task_delay, mock_redis, mock_whatsapp_payload):
    # Mock the media download, storage upload, and the Celery task delay
    mock_download.return_value = b"fake_image_bytes"
    mock_upload.return_value = "fake_storage_key"
    mock_redis_client = mock_redis.return_value
    mock_redis_client.set.return_value = True
    
    # Prepare the payload and signature
    payload_json = json.dumps(mock_whatsapp_payload)
    payload_bytes = payload_json.encode('utf-8')
    signature = generate_wa_signature(payload_bytes, settings.WHATSAPP_WEBHOOK_SECRET)
    
    # Trigger the webhook
    response = client.post(
        "/webhooks/whatsapp",
        content=payload_bytes,
        headers={"X-Hub-Signature-256": signature, "Content-Type": "application/json"}
    )
    
    # Assert 1: Meta webhook immediately gets a 200 OK
    assert response.status_code == 200
    
    # Assert 2: The celery task was successfully queued
    mock_task_delay.assert_called_once()
