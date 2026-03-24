import razorpay  # type: ignore
import hmac
import hashlib
from app.config import settings  # type: ignore

# Initialize Razorpay client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))  # type: ignore

# Map internal plan names to Razorpay Plan IDs (created in Razorpay Dashboard)
PLAN_MAPPING = {
    'starter': 'plan_starter_id_123',
    'professional': 'plan_pro_id_456',
    'enterprise': 'plan_ent_id_789'
}

class RazorpayService:
    @staticmethod
    def create_subscription(plan_name: str, total_count: int = 12) -> dict:
        plan_id = PLAN_MAPPING.get(plan_name)
        if not plan_id:
            raise ValueError(f"Invalid plan selected: {plan_name}")
            
        subscription = client.subscription.create({
            "plan_id": plan_id,
            "total_count": total_count,
            "customer_notify": 1
        })
        return {
            "subscription_id": subscription['id'],
            "short_url": subscription.get('short_url')
        }

    @staticmethod
    def verify_webhook_signature(payload_body: bytes, signature: str) -> bool:
        secret = settings.RAZORPAY_WEBHOOK_SECRET
        if not secret:
            # If not configured, fail signature check for safety
            return False
            
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload_body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
