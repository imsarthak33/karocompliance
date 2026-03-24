from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.ca_firm import CAFirm
from app.utils.security import get_current_ca_firm
from app.services.razorpay_service import RazorpayService

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/create-subscription")
async def create_subscription(
    plan: str, 
    ca_firm: CAFirm = Depends(get_current_ca_firm), 
    db: Session = Depends(get_db)
):
    try:
        sub_data = RazorpayService.create_subscription(plan)
        # Store pending subscription ID
        ca_firm.razorpay_subscription_id = sub_data['subscription_id']
        db.commit()
        return sub_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")
    
    if not signature or not RazorpayService.verify_webhook_signature(payload, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
        
    data = await request.json()
    event = data.get('event')
    sub_id = data['payload']['subscription']['entity']['id']
    
    ca_firm = db.query(CAFirm).filter(CAFirm.razorpay_subscription_id == sub_id).first()
    if not ca_firm:
        return {"status": "ignored", "reason": "unknown subscription"}

    if event == 'subscription.charged':
        ca_firm.is_active = True
        # Note: You could map the Plan ID back to the plan name here if needed.
    elif event == 'subscription.halted':
        ca_firm.subscription_plan = 'trial' # Downgrade or pause
    elif event == 'subscription.cancelled':
        ca_firm.is_active = False

    db.commit()
    return {"status": "success"}
