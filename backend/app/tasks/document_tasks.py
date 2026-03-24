import asyncio
import logging
from app.celery_app import celery_app  # type: ignore
from app.database import SessionLocal  # type: ignore
from app.agents.nemoclaw_orchestrator import NemoClawOrchestrator  # type: ignore

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_incoming_document(self, document_id: str):
    """
    Main background task to process documents via NVIDIA NemoClaw.
    The task is synchronous but calls the asynchronous NemoClaw orchestrator.
    """
    db = SessionLocal()
    try:
        logger.info(f"NemoClaw Task Started: Processing document {document_id}")
        orchestrator = NemoClawOrchestrator(db)
        
        # In modern Python, you'd use a loop managed at the process level or 
        # a dedicated async worker, but for standard Celery, asyncio.run is the bridge.
        result = asyncio.run(orchestrator.run(document_id))
        
        logger.info(f"NemoClaw Task Finished: Document {document_id} result: {result.status}")  # type: ignore
        return {"status": result.status, "document_id": document_id}  # type: ignore
        
    except Exception as exc:
        logger.error(f"NemoClaw Task Failed: {str(exc)}")
        # If the failure is transient (e.g. LLM rate limit), retry the task.
        raise self.retry(exc=exc)
    finally:
        db.close()
