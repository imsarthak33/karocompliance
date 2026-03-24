import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey, Date, Numeric  # type: ignore
from sqlalchemy.dialects.postgresql import UUID  # type: ignore
from app.database import Base  # type: ignore

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'), nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey('clients.id'), nullable=False)
    ca_firm_id = Column(UUID(as_uuid=True), ForeignKey('ca_firms.id'), nullable=False)
    transaction_type = Column(Enum('purchase', 'sale', 'bank_debit', 'bank_credit', name='txn_type_enum'))
    invoice_number = Column(String(100))
    invoice_date = Column(Date)
    vendor_gstin = Column(String(15))
    vendor_name = Column(String(300))
    hsn_sac_code = Column(String(20))
    taxable_value = Column(Numeric(15,2))
    cgst_amount = Column(Numeric(15,2))
    sgst_amount = Column(Numeric(15,2))
    igst_amount = Column(Numeric(15,2))
    total_amount = Column(Numeric(15,2))
    gst_rate = Column(Numeric(5,2))
    is_itc_eligible = Column(Boolean)
    gstr2b_matched = Column(Boolean, default=False)
    gstr2b_mismatch_reason = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
