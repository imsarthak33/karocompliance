"""
Documents Router — Tenant-isolated document listing.

Strict Mandates:
  • Hard tenant isolation via ca_firm_id filter
  • Pydantic response_model
  • Authenticated endpoints
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict  # type: ignore
from fastapi import APIRouter, Depends  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.database import get_db  # type: ignore
from app.models.ca_firm import CAFirm  # type: ignore
from app.models.document import Document  # type: ignore
from app.utils.security import get_current_ca_firm  # type: ignore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: UUID
    ca_firm_id: UUID
    client_id: UUID
    whatsapp_message_id: Optional[str] = None
    document_type: Optional[str] = None
    original_file_name: Optional[str] = None
    storage_key: str
    file_format: Optional[str] = None
    processing_status: Optional[str] = None
    processing_error: Optional[str] = None
    confidence_score: Optional[Decimal] = None
    requires_manual_review: Optional[bool] = False
    review_reason: Optional[str] = None
    received_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    ca_firm: CAFirm = Depends(get_current_ca_firm),
    db: Session = Depends(get_db),
):
    """Returns all documents for the authenticated CA firm only (tenant-isolated)."""
    documents = (
        db.query(Document)
        .filter(Document.ca_firm_id == ca_firm.id)
        .order_by(Document.received_at.desc())
        .all()
    )
    logger.info("Listed %d documents for firm %s", len(documents), ca_firm.id)
    return documents
