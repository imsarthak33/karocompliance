import os
import hmac
import hashlib
import json
import uuid
from fastapi import APIRouter, Request, Header, HTTPException, Depends  # type: ignore
from fastapi.responses import JSONResponse  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from app.database import get_db  # type: ignore
from app.models.ca_firm import CAFirm  # type: ignore
from app.models.client import Client  # type: ignore
from app.models.document import Document  # type: ignore
from app.services.whatsapp_service import download_media  # type: ignore
from app.services.storage_service import upload_document  # type: ignore
from app.tasks.document_tasks import process_incoming_document  # type: ignore

router = APIRouter()
WHATSAPP_WEBHOOK_SECRET = os.getenv("WHATSAPP_WEBHOOK_SECRET")

def verify_signature(payload: bytes, signature: str):
    """STEP 1: Validate X-Hub-Signature-256."""
    if not signature or not signature.startswith("sha256="):
        raise HTTPException(status_code=403, detail="Invalid signature format")
    
    signature_hash = signature.split("sha256=")[1]
    expected_hash = hmac.new(
        key=WHATSAPP_WEBHOOK_SECRET.encode('utf-8') if WHATSAPP_WEBHOOK_SECRET else b"",
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(expected_hash, signature_hash):
        raise HTTPException(status_code=403, detail="Signature mismatch")

@router.get("/whatsapp")
async def verify_webhook(request: Request):
    """Meta requires a GET request setup to verify the webhook URL."""
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "karo_setup_token")
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == verify_token:
        try:
            return int(challenge)
        except (ValueError, TypeError):
            return challenge
    raise HTTPException(status_code=403, detail="Invalid verification token")

@router.post("/whatsapp")
async def receive_whatsapp_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
    db: Session = Depends(get_db)
):
    # Always return 200 to prevent Meta from retrying, even if we fail internally.
    try:
        # STEP 1: Verify webhook signature
        raw_body = await request.body()
        if WHATSAPP_WEBHOOK_SECRET:
            verify_signature(raw_body, x_hub_signature_256)
        
        # STEP 2: Parse incoming payload
        data = json.loads(raw_body)
        
        # Extract metadata
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

        # STEP 3: Identify the CA firm
        ca_firm = db.query(CAFirm).filter(CAFirm.whatsapp_number_assigned == destination_number_id).first()
        if not ca_firm:
            return JSONResponse(content={"status": "firm_not_found"}, status_code=200)

        # STEP 4: Identify or create the client
        client = db.query(Client).filter(
            Client.ca_firm_id == ca_firm.id,
            Client.phone_whatsapp == sender_wa_id
        ).first()
        
        if not client:
            client = Client(
                ca_firm_id=ca_firm.id,
                client_name="Pending Onboarding",
                phone_whatsapp=sender_wa_id,
                gstin="PENDING",
                onboarded_to_whatsapp=False
            )
            db.add(client)
            db.commit()
            db.refresh(client)

        # STEP 5: Check idempotency
        existing_doc = db.query(Document).filter(Document.whatsapp_message_id == message_id).first()
        if existing_doc:
            return JSONResponse(content={"status": "duplicate"}, status_code=200)

        # STEP 6: Download media and upload to Cloud Storage
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
            storage_key = await upload_document(media_bytes, file_name, folder=str(ca_firm.id))
            
            # Create Document Record
            new_document = Document(
                ca_firm_id=ca_firm.id,
                client_id=client.id,
                whatsapp_message_id=message_id,
                storage_key=storage_key,
                processing_status="queued"
            )
            db.add(new_document)
            db.commit()
            db.refresh(new_document)

            process_incoming_document.delay(str(new_document.id))

        return JSONResponse(content={"status": "success"}, status_code=200)
        
    except Exception as e:
        print(f"Webhook Error: {str(e)}")
        return JSONResponse(content={"status": "error_handled"}, status_code=200)
