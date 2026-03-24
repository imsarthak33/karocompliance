"""
Clients Router — Tenant-isolated client management.

Strict Mandates:
  • Hard tenant isolation via ca_firm_id filter
  • Pydantic response_model
  • Authenticated endpoints
"""
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict  # type: ignore
from fastapi import APIRouter, Depends  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.database import get_db  # type: ignore
from app.models.ca_firm import CAFirm  # type: ignore
from app.models.client import Client  # type: ignore
from app.utils.security import get_current_ca_firm  # type: ignore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clients", tags=["Clients"])


class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ca_firm_id: UUID
    client_name: str
    gstin: str
    trade_name: Optional[str] = None
    phone_whatsapp: str
    email: Optional[str] = None
    filing_frequency: Optional[str] = None
    gst_registration_type: Optional[str] = None
    state_code: Optional[str] = None
    is_active: Optional[bool] = True
    last_document_received_at: Optional[datetime] = None
    last_filed_at: Optional[datetime] = None
    onboarded_to_whatsapp: Optional[bool] = False
    created_at: Optional[datetime] = None


@router.get("/", response_model=list[ClientResponse])
async def list_clients(
    ca_firm: CAFirm = Depends(get_current_ca_firm),
    db: Session = Depends(get_db),
):
    """Returns all clients for the authenticated CA firm only (tenant-isolated)."""
    clients = (
        db.query(Client)
        .filter(Client.ca_firm_id == ca_firm.id)
        .all()
    )
    logger.info("Listed %d clients for firm %s", len(clients), ca_firm.id)
    return clients
