import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum  # type: ignore
from sqlalchemy.dialects.postgresql import UUID  # type: ignore
from app.database import Base  # type: ignore

class CAFirm(Base):
    __tablename__ = "ca_firms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supabase_user_id = Column(String, index=True)
    firm_name = Column(String(200), nullable=False)
    ca_name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    phone = Column(String(15), nullable=False)
    icai_membership_number = Column(String(50))
    whatsapp_number_assigned = Column(String(15), unique=True)
    gstin = Column(String(15))
    subscription_plan = Column(Enum('trial', 'starter', 'professional', 'enterprise', name='subscription_plan_enum'), default='trial')
    razorpay_subscription_id = Column(String(100))
    trial_ends_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    onboarding_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
