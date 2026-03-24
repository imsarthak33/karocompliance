import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey  # type: ignore
from sqlalchemy.dialects.postgresql import UUID  # type: ignore
from app.database import Base  # type: ignore

class Client(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ca_firm_id = Column(UUID(as_uuid=True), ForeignKey('ca_firms.id'), nullable=False)
    client_name = Column(String(200), nullable=False)
    gstin = Column(String(15), unique=True, nullable=False)
    trade_name = Column(String(200))
    phone_whatsapp = Column(String(15), nullable=False)
    email = Column(String(200))
    filing_frequency = Column(Enum('monthly', 'quarterly', name='filing_freq_enum'), default='monthly')
    gst_registration_type = Column(Enum('regular', 'composition', 'exempt', name='gst_reg_type_enum'))
    state_code = Column(String(2))
    is_active = Column(Boolean, default=True)
    last_document_received_at = Column(DateTime)
    last_filed_at = Column(DateTime)
    onboarded_to_whatsapp = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
