import logging
from sqlalchemy.orm import Session  # type: ignore
from app.models.document import Document  # type: ignore
from app.services import s3_service, ocr_service  # type: ignore
from app.agents.classifier_agent import ClassifierAgent  # type: ignore
from app.agents.extraction_agent import ExtractionAgent  # type: ignore
from app.agents.voice_agent import VoiceAgent  # type: ignore
from app.agents.reconciliation_agent import ReconciliationAgent  # type: ignore
from app.agents.communication_agent import CommunicationAgent  # type: ignore

# Using NVIDIA NemoClaw architecture: https://github.com/NVIDIA/NemoClaw.git
logger = logging.getLogger(__name__)

class ProcessingResult:
    def __init__(self, status: str, error: str | None = None):
        self.status = status
        self.error = error

class NemoClawOrchestrator:
    def __init__(self, db: Session):
        self.db = db

    async def run(self, document_id: str) -> ProcessingResult:
        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return ProcessingResult('failed', 'Document not found in DB')

        try:
            doc.processing_status = 'processing'
            self.db.commit()

            file_bytes = await s3_service.download_file(doc.s3_key)

            # ROUTER LOGIC
            if doc.file_format == 'audio':
                result = await self._run_voice_workflow(doc, file_bytes)
            elif doc.file_format == 'pdf':
                result = await self._run_pdf_workflow(doc, file_bytes)
            elif doc.file_format == 'image':
                result = await self._run_image_workflow(doc, file_bytes)
            elif doc.file_format == 'excel':
                result = await self._run_excel_workflow(doc, file_bytes)
            else:
                doc.processing_status = 'failed'
                doc.processing_error = 'Unsupported format'
                self.db.commit()
                return ProcessingResult('failed', 'Unsupported format')

            # Complete
            doc.processing_status = 'extracted'
            self.db.commit()
            
            # Alert CA Firm async
            await CommunicationAgent.send_anomaly_alert_to_ca(str(doc.ca_firm_id), f"Document {doc.id} processed successfully.")
            return ProcessingResult('extracted')

        except Exception as e:
            logger.error(f"NemoClaw Orchestrator failed on doc {document_id}: {str(e)}")
            doc.processing_status = 'failed'
            doc.processing_error = str(e)
            self.db.commit()
            return ProcessingResult('failed', str(e))

    async def _run_voice_workflow(self, doc: Document, file_bytes: bytes):
        transcription = await VoiceAgent.transcribe(file_bytes)
        doc.extracted_data = {"transcript": transcription.transcript}

    async def _run_pdf_workflow(self, doc: Document, file_bytes: bytes):
        ocr_text = await ocr_service.extract_pdf_text(file_bytes)
        classification = await ClassifierAgent.classify_pdf(ocr_text, doc.original_file_name)
        doc.document_type = classification.type

        if classification.type in ['purchase_invoice', 'sale_invoice']:
            extracted = await ExtractionAgent.parse_invoice(ocr_text, classification.type)
            doc.extracted_data = extracted.model_dump()
        elif classification.type == 'bank_statement':
            extracted = await ExtractionAgent.parse_bank_statement(ocr_text)
            doc.extracted_data = {"transactions": [tx.model_dump() for tx in extracted]}
        elif classification.type == 'unknown':
            doc.requires_manual_review = True
            doc.review_reason = classification.reasoning

    async def _run_image_workflow(self, doc: Document, file_bytes: bytes):
        classification = await ClassifierAgent.classify_image(file_bytes)
        doc.document_type = classification.type
        ocr_text = await ocr_service.extract_image_text(file_bytes)
        
        if classification.type in ['purchase_invoice', 'sale_invoice']:
            extracted = await ExtractionAgent.parse_invoice(ocr_text, classification.type)
            doc.extracted_data = extracted.model_dump()

    async def _run_excel_workflow(self, doc: Document, file_bytes: bytes):
        extracted = await ExtractionAgent.parse_excel_register(file_bytes)
        doc.extracted_data = {"rows_extracted": len(extracted), "data": extracted}
