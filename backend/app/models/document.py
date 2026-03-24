import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum, ForeignKey, Float, Text  # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB  # type: ignore
from app.database import Base  # type: ignore

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ca_firm_id = Column(UUID(as_uuid=True), ForeignKey('ca_firms.id'), nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey('clients.id'), nullable=False)
    whatsapp_message_id = Column(String(100), unique=True)
    document_type = Column(Enum('purchase_invoice', 'sale_invoice', 'bank_statement', 'credit_note', 'debit_note', 'voice_note', 'unknown', name='doc_type_enum'))
    original_file_name = Column(String(300))
    s3_key = Column(String(500), nullable=False)
    s3_signed_url = Column(String(1000))
    file_format = Column(Enum('pdf', 'image', 'excel', 'audio', 'unknown', name='file_format_enum'))
    file_size_bytes = Column(Integer)
    processing_status = Column(Enum('received', 'queued', 'processing', 'extracted', 'reconciled', 'failed', 'flagged', name='proc_status_enum'))
    processing_error = Column(Text)
    extracted_data = Column(JSONB)
    confidence_score = Column(Float)
    requires_manual_review = Column(Boolean, default=False)
    review_reason = Column(Text)
    tax_period_month = Column(Integer)
    tax_period_year = Column(Integer)
    received_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
