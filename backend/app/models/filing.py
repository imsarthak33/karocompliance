import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Date, Numeric  # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB  # type: ignore
from app.database import Base  # type: ignore

class Filing(Base):
    __tablename__ = "filings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey('clients.id'), nullable=False)
    ca_firm_id = Column(UUID(as_uuid=True), ForeignKey('ca_firms.id'), nullable=False)
    return_type = Column(Enum('GSTR1', 'GSTR3B', 'GSTR9', 'GSTR2B_RECON', name='return_type_enum'))
    tax_period_month = Column(Integer)
    tax_period_year = Column(Integer)
    due_date = Column(Date)
    status = Column(Enum('pending_documents', 'documents_received', 'draft_ready', 'ca_review', 'filed', 'overdue', name='filing_status_enum'))
    draft_json = Column(JSONB)
    filed_at = Column(DateTime)
    arn_number = Column(String(50))
    total_tax_liability = Column(Numeric(15,2))
    itc_claimed = Column(Numeric(15,2))
    net_payable = Column(Numeric(15,2))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
