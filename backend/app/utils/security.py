"""
Security Utilities — JWT validation and tenant-scoped auth dependencies.

Strict Mandates:
  • Validate JWT `exp` claim (prevent expired token reuse)
  • Use datetime.now(timezone.utc) instead of deprecated datetime.utcnow()
  • Sentry breadcrumbs for auth failures
"""
import logging
from datetime import datetime, timezone

import sentry_sdk  # type: ignore
from fastapi import Depends, HTTPException, status  # type: ignore
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from jose import jwt, JWTError, ExpiredSignatureError  # type: ignore

from app.database import get_db  # type: ignore
from app.models.ca_firm import CAFirm  # type: ignore
from app.config import settings  # type: ignore

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_ca_firm(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> CAFirm:
    """
    Validate JWT, extract Supabase user ID, and return the corresponding CA firm.

    This is the primary tenant-isolation boundary — every authenticated endpoint
    receives the CA firm scoped to the JWT bearer, preventing cross-tenant access.
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={
                "verify_exp": True,
                "verify_aud": False,
            },
        )
    except ExpiredSignatureError:
        logger.warning("Expired JWT token rejected")
        sentry_sdk.set_context("auth_failure", {"reason": "expired_token"})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except JWTError as e:
        logger.warning("Invalid JWT token rejected: %s", e)
        sentry_sdk.set_context("auth_failure", {"reason": "invalid_token", "error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    supabase_user_id = payload.get("sub")
    if supabase_user_id is None:
        logger.warning("JWT missing 'sub' claim")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing subject",
        )

    ca_firm = db.query(CAFirm).filter(CAFirm.supabase_user_id == supabase_user_id).first()
    if not ca_firm:
        logger.warning("No CA firm found for Supabase user: %s", supabase_user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CA Firm profile not found",
        )

    return ca_firm


def require_active_subscription(
    ca_firm: CAFirm = Depends(get_current_ca_firm),
) -> CAFirm:
    """Require an active subscription or valid trial period."""
    if not ca_firm.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    if ca_firm.subscription_plan == "trial":
        if ca_firm.trial_ends_at and ca_firm.trial_ends_at.replace(
            tzinfo=timezone.utc
        ) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Trial expired. Subscription required to access this feature.",
            )

    # For active paid plans, we rely on the Razorpay webhook to downgrade if payment fails.
    return ca_firm
