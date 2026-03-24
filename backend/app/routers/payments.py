"""
Payments Router — Razorpay subscription management.

Strict Mandates:
  • Pydantic response_model
  • Sentry error tracking
  • Authenticated endpoints
"""
import logging
from typing import Optional

import sentry_sdk  # type: ignore
from pydantic import BaseModel  # type: ignore
from fastapi import APIRouter, Depends, Request, HTTPException  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.database import get_db  # type: ignore
from app.models.ca_firm import CAFirm  # type: ignore
from app.utils.security import get_current_ca_firm  # type: ignore
from app.services.razorpay_service import RazorpayService  # type: ignore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------
class CreateSubscriptionResponse(BaseModel):
    subscription_id: str
    short_url: Optional[str] = None


class WebhookStatusResponse(BaseModel):
    status: str
    reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/create-subscription", response_model=CreateSubscriptionResponse)
async def create_subscription(
    plan: str,
    ca_firm: CAFirm = Depends(get_current_ca_firm),
    db: Session = Depends(get_db),
):
    try:
        sub_data = RazorpayService.create_subscription(plan)
        ca_firm.razorpay_subscription_id = sub_data["subscription_id"]
        db.commit()
        logger.info("Subscription created for firm %s: %s", ca_firm.id, sub_data["subscription_id"])
        return CreateSubscriptionResponse(**sub_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Failed to create subscription for firm %s", ca_firm.id)
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail="Subscription creation failed")


@router.post("/webhook", response_model=WebhookStatusResponse)
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")

    if not signature or not RazorpayService.verify_webhook_signature(payload, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = await request.json()
    event = data.get("event")
    sub_id = data["payload"]["subscription"]["entity"]["id"]

    ca_firm = db.query(CAFirm).filter(CAFirm.razorpay_subscription_id == sub_id).first()
    if not ca_firm:
        logger.info("Razorpay webhook for unknown subscription: %s", sub_id)
        return WebhookStatusResponse(status="ignored", reason="unknown subscription")

    if event == "subscription.charged":
        ca_firm.is_active = True
        logger.info("Subscription charged for firm %s", ca_firm.id)
    elif event == "subscription.halted":
        ca_firm.subscription_plan = "trial"
        logger.warning("Subscription halted for firm %s — downgraded to trial", ca_firm.id)
    elif event == "subscription.cancelled":
        ca_firm.is_active = False
        logger.warning("Subscription cancelled for firm %s", ca_firm.id)

    db.commit()
    return WebhookStatusResponse(status="success")
