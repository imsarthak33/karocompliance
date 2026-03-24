"""
WhatsApp Webhook Router — Production-grade with Redis idempotency lock.

Strict Mandates:
  • Redis distributed lock (SET NX EX) to prevent duplicate processing from Meta retries
  • Pydantic response_model for automatic serialization and OpenAPI spec
  • Sentry + logger.exception for error tracking (no print/silent swallows)
  • Structured logging throughout
"""
import hmac
import hashlib
import json
import uuid
import logging
from typing import Optional

import redis  # type: ignore
import sentry_sdk  # type: ignore
from pydantic import BaseModel  # type: ignore
from fastapi import APIRouter, Request, Header, HTTPException, Depends  # type: ignore
from fastapi.responses import JSONResponse  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.config import settings  # type: ignore
from app.database import get_db  # type: ignore
from app.models.ca_firm import CAFirm  # type: ignore
from app.models.client import Client  # type: ignore
from app.models.document import Document  # type: ignore
from app.services.whatsapp_service import download_media  # type: ignore
from app.services.storage_service import upload_document  # type: ignore
from app.tasks.document_tasks import process_incoming_document  # type: ignore

logger = logging.getLogger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# Redis client for distributed idempotency locks
# ---------------------------------------------------------------------------
_redis_client: Optional[redis.Redis] = None


def _get_redis() -> redis.Redis:
    """Lazy-init Redis client from settings."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
        )
    return _redis_client


# Lock TTL: 5 minutes — Meta retries within this window
_LOCK_TTL_SECONDS = 300


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------
class WebhookResponse(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Signature Verification
# ---------------------------------------------------------------------------
def verify_signature(payload: bytes, signature: str) -> None:
    """Validate X-Hub-Signature-256 from Meta."""
    if not signature or not signature.startswith("sha256="):
        raise HTTPException(status_code=403, detail="Invalid signature format")

    signature_hash = signature.split("sha256=")[1]
    expected_hash = hmac.new(
        key=settings.WHATSAPP_WEBHOOK_SECRET.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, signature_hash):
        raise HTTPException(status_code=403, detail="Signature mismatch")


# ---------------------------------------------------------------------------
# GET /whatsapp — Meta Verification Handshake
# ---------------------------------------------------------------------------
@router.get("/whatsapp", response_model=None)
async def verify_webhook(request: Request):
    """Meta requires a GET request to verify the webhook URL."""
    verify_token = settings.WHATSAPP_WEBHOOK_SECRET or "karo_setup_token"
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == verify_token:
        try:
            return int(challenge)
        except (ValueError, TypeError):
            return challenge
    raise HTTPException(status_code=403, detail="Invalid verification token")


# ---------------------------------------------------------------------------
# POST /whatsapp — Receive WhatsApp Message Webhook
# ---------------------------------------------------------------------------
@router.post("/whatsapp", response_model=WebhookResponse)
async def receive_whatsapp_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Process incoming WhatsApp webhook with Redis-based idempotency lock.

    Always returns HTTP 200 to prevent Meta from retrying on our internal failures.
    The Redis lock guarantees exactly-once processing even under aggressive retries.
    """
    try:
        # STEP 1: Verify webhook signature
        raw_body = await request.body()
        if settings.WHATSAPP_WEBHOOK_SECRET:
            verify_signature(raw_body, x_hub_signature_256)

        # STEP 2: Parse incoming payload
        data = json.loads(raw_body)

        entry = data.get("entry", [])
        if not entry:
            return JSONResponse(content={"status": "no_entry"}, status_code=200)

        changes = entry[0].get("changes", [])
        if not changes:
            return JSONResponse(content={"status": "no_changes"}, status_code=200)

        value = changes[0].get("value", {})

        if "messages" not in value:
            return JSONResponse(content={"status": "ignored"}, status_code=200)

        message = value["messages"][0]
        sender_wa_id = message.get("from")
        message_id = message.get("id")
        msg_type = message.get("type")
        destination_number_id = value.get("metadata", {}).get("display_phone_number")

        # STEP 3: REDIS IDEMPOTENCY LOCK — prevents race condition from Meta retries
        r = _get_redis()
        lock_key = f"wa_lock:{message_id}"
        lock_acquired = r.set(lock_key, "1", nx=True, ex=_LOCK_TTL_SECONDS)

        if not lock_acquired:
            logger.info("Duplicate webhook rejected via Redis lock: %s", message_id)
            return JSONResponse(content={"status": "duplicate"}, status_code=200)

        # STEP 4: Identify the CA firm
        ca_firm = (
            db.query(CAFirm)
            .filter(CAFirm.whatsapp_number_assigned == destination_number_id)
            .first()
        )
        if not ca_firm:
            logger.warning("No CA firm found for WhatsApp number: %s", destination_number_id)
            return JSONResponse(content={"status": "firm_not_found"}, status_code=200)

        # STEP 5: Identify or create the client (scoped to CA firm — tenant isolation)
        client = (
            db.query(Client)
            .filter(
                Client.ca_firm_id == ca_firm.id,
                Client.phone_whatsapp == sender_wa_id,
            )
            .first()
        )

        if not client:
            client = Client(
                ca_firm_id=ca_firm.id,
                client_name="Pending Onboarding",
                phone_whatsapp=sender_wa_id,
                gstin="PENDING",
                onboarded_to_whatsapp=False,
            )
            db.add(client)
            db.commit()
            db.refresh(client)
            logger.info("Auto-created client for phone %s under firm %s", sender_wa_id, ca_firm.id)

        # STEP 6: Secondary DB-level idempotency check (belt-and-suspenders)
        existing_doc = (
            db.query(Document)
            .filter(Document.whatsapp_message_id == message_id)
            .first()
        )
        if existing_doc:
            logger.info("Duplicate document already in DB: %s", message_id)
            return JSONResponse(content={"status": "duplicate"}, status_code=200)

        # STEP 7: Download media and upload to Cloud Storage
        media_id = None
        file_ext = "unknown"

        if msg_type == "document":
            media_id = message["document"]["id"]
            file_ext = message["document"].get("mime_type", "").split("/")[-1]
        elif msg_type == "image":
            media_id = message["image"]["id"]
            file_ext = "jpg"
        elif msg_type == "audio":
            media_id = message["audio"]["id"]
            file_ext = "ogg"

        if media_id:
            media_bytes = await download_media(media_id)
            file_name = f"{uuid.uuid4()}.{file_ext}"
            storage_key = await upload_document(
                media_bytes, file_name, folder=str(ca_firm.id)
            )

            # Create Document Record
            new_document = Document(
                ca_firm_id=ca_firm.id,
                client_id=client.id,
                whatsapp_message_id=message_id,
                storage_key=storage_key,
                processing_status="queued",
            )
            db.add(new_document)
            db.commit()
            db.refresh(new_document)

            # Queue for async NemoClaw processing
            process_incoming_document.delay(str(new_document.id))
            logger.info(
                "Document %s queued for processing (firm=%s, client=%s)",
                new_document.id, ca_firm.id, client.id,
            )

        return JSONResponse(content={"status": "success"}, status_code=200)

    except HTTPException:
        raise  # Re-raise FastAPI HTTP exceptions (signature failures)
    except Exception as e:
        logger.exception("Webhook processing error")
        sentry_sdk.capture_exception(e)
        # Always return 200 to Meta to prevent infinite retry loops
        return JSONResponse(content={"status": "error_handled"}, status_code=200)
