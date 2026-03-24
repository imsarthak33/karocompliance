from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.ca_firm import CAFirm
from jose import jwt, JWTError
from app.config import settings

security = HTTPBearer()

async def get_current_ca_firm(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> CAFirm:
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.SUPABASE_JWT_SECRET, 
            algorithms=["HS256"], 
            options={"verify_aud": False}
        )
        supabase_user_id = payload.get("sub")
        if supabase_user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    ca_firm = db.query(CAFirm).filter(CAFirm.supabase_user_id == supabase_user_id).first()
    if not ca_firm:
        raise HTTPException(status_code=401, detail="CA Firm profile not found")
        
    return ca_firm

def require_active_subscription(ca_firm: CAFirm = Depends(get_current_ca_firm)) -> CAFirm:
    if not ca_firm.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
        
    if ca_firm.subscription_plan == 'trial':
        if ca_firm.trial_ends_at and ca_firm.trial_ends_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED, 
                detail="Trial expired. Subscription required to access this feature."
            )
            
    # For active paid plans, we rely on the webhook to downgrade them if payment fails.
    return ca_firm
