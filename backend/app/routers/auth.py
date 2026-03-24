"""
Auth Router — Authenticated CA firm profile endpoint.

Strict Mandates:
  • Pydantic response_model
  • Wired to get_current_ca_firm dependency
"""
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict  # type: ignore
from fastapi import APIRouter, Depends  # type: ignore

from app.models.ca_firm import CAFirm  # type: ignore
from app.utils.security import get_current_ca_firm  # type: ignore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


class CAFirmProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    firm_name: str
    ca_name: str
    email: str
    phone: str
    icai_membership_number: Optional[str] = None
    whatsapp_number_assigned: Optional[str] = None
    gstin: Optional[str] = None
    subscription_plan: Optional[str] = None
    trial_ends_at: Optional[datetime] = None
    is_active: Optional[bool] = True
    onboarding_completed: Optional[bool] = False
    created_at: Optional[datetime] = None


@router.get("/me", response_model=CAFirmProfile)
async def get_me(ca_firm: CAFirm = Depends(get_current_ca_firm)):
    """Returns the authenticated CA firm's profile."""
    logger.info("Profile accessed for firm %s", ca_firm.id)
    return ca_firm
