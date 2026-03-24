"""
NemoClaw Orchestrator — Multi-agent document processing pipeline.

Strict Mandates:
  • Sentry span tracing across the full pipeline
  • Explicit error logging with sentry_sdk
  • No silent failure swallows
"""
import logging

import sentry_sdk  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.models.document import Document  # type: ignore
from app.services import storage_service, ocr_service  # type: ignore
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
        with sentry_sdk.start_span(
            op="orchestrator.nemoclaw", description=f"process_document:{document_id}"
        ) as span:
            span.set_data("document_id", document_id)

            doc = self.db.query(Document).filter(Document.id == document_id).first()
            if not doc:
                logger.error("Document not found in DB: %s", document_id)
                return ProcessingResult("failed", "Document not found in DB")

            try:
                doc.processing_status = "processing"
                self.db.commit()

                file_bytes = await storage_service.download_file(doc.storage_key)
                span.set_data("file_format", doc.file_format)
                span.set_data("file_size_bytes", len(file_bytes))

                # ROUTER LOGIC
                if doc.file_format == "audio":
                    await self._run_voice_workflow(doc, file_bytes)
                elif doc.file_format == "pdf":
                    await self._run_pdf_workflow(doc, file_bytes)
                elif doc.file_format == "image":
                    await self._run_image_workflow(doc, file_bytes)
                elif doc.file_format == "excel":
                    await self._run_excel_workflow(doc, file_bytes)
                else:
                    doc.processing_status = "failed"
                    doc.processing_error = "Unsupported format"
                    self.db.commit()
                    span.set_data("result", "unsupported_format")
                    return ProcessingResult("failed", "Unsupported format")

                # Complete
                doc.processing_status = "extracted"
                self.db.commit()

                # Alert CA Firm async
                await CommunicationAgent.send_anomaly_alert_to_ca(
                    str(doc.ca_firm_id), f"Document {doc.id} processed successfully."
                )

                span.set_data("result", "extracted")
                logger.info("NemoClaw: document %s processed successfully", document_id)
                return ProcessingResult("extracted")

            except Exception as e:
                logger.exception("NemoClaw Orchestrator failed on doc %s", document_id)
                sentry_sdk.capture_exception(e)
                doc.processing_status = "failed"
                doc.processing_error = str(e)
                self.db.commit()
                return ProcessingResult("failed", str(e))

    async def _run_voice_workflow(self, doc: Document, file_bytes: bytes) -> None:
        with sentry_sdk.start_span(op="workflow.voice", description="voice_pipeline"):
            transcription = await VoiceAgent.transcribe(file_bytes)
            doc.extracted_data = {"transcript": transcription.transcript}

    async def _run_pdf_workflow(self, doc: Document, file_bytes: bytes) -> None:
        with sentry_sdk.start_span(op="workflow.pdf", description="pdf_pipeline"):
            ocr_text = await ocr_service.extract_pdf_text(file_bytes)
            classification = await ClassifierAgent.classify_pdf(ocr_text, doc.original_file_name)
            doc.document_type = classification.type

            if classification.type in ["purchase_invoice", "sale_invoice"]:
                extracted = await ExtractionAgent.parse_invoice(ocr_text, classification.type)
                doc.extracted_data = extracted.model_dump(mode="json")
            elif classification.type == "bank_statement":
                extracted = await ExtractionAgent.parse_bank_statement(ocr_text)
                doc.extracted_data = {
                    "transactions": [tx.model_dump(mode="json") for tx in extracted]
                }
            elif classification.type == "unknown":
                doc.requires_manual_review = True
                doc.review_reason = classification.reasoning

    async def _run_image_workflow(self, doc: Document, file_bytes: bytes) -> None:
        with sentry_sdk.start_span(op="workflow.image", description="image_pipeline"):
            classification = await ClassifierAgent.classify_image(file_bytes)
            doc.document_type = classification.type
            ocr_text = await ocr_service.extract_image_text(file_bytes)

            if classification.type in ["purchase_invoice", "sale_invoice"]:
                extracted = await ExtractionAgent.parse_invoice(ocr_text, classification.type)
                doc.extracted_data = extracted.model_dump(mode="json")

    async def _run_excel_workflow(self, doc: Document, file_bytes: bytes) -> None:
        with sentry_sdk.start_span(op="workflow.excel", description="excel_pipeline"):
            extracted = await ExtractionAgent.parse_excel_register(file_bytes)
            doc.extracted_data = {"rows_extracted": len(extracted), "data": extracted}
