import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey, Text  # type: ignore
from sqlalchemy.dialects.postgresql import UUID  # type: ignore
from app.database import Base  # type: ignore

class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey('clients.id'), nullable=False)
    ca_firm_id = Column(UUID(as_uuid=True), ForeignKey('ca_firms.id'), nullable=False)
    filing_id = Column(UUID(as_uuid=True), ForeignKey('filings.id'), nullable=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'), nullable=True)
    anomaly_type = Column(Enum('itc_mismatch', 'missing_invoice', 'duplicate_invoice', 'rate_mismatch', 'supplier_non_filer', 'data_quality', 'deadline_risk', 'high_value_transaction', name='anomaly_type_enum'))
    severity = Column(Enum('low', 'medium', 'high', 'critical', name='severity_enum'))
    description = Column(Text)
    suggested_action = Column(Text)
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String(200))
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
