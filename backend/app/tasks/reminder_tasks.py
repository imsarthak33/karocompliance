import logging
from datetime import datetime
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.filing import Filing
from app.models.client import Client
from app.models.ca_firm import CAFirm
from app.agents.communication_agent import CommunicationAgent

logger = logging.getLogger(__name__)

@celery_app.task
def send_daily_reminders():
    """Runs daily to chase clients for upcoming filing deadlines."""
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        
        # Find filings that are due soon but not yet filed or draft_ready
        active_filings = db.query(Filing).filter(
            Filing.status.in_(['pending_documents', 'documents_received']),
            Filing.due_date >= today
        ).all()

        for filing in active_filings:
            days_to_deadline = (filing.due_date - today).days
            
            # Send reminders at specific intervals: 10, 5, and 2 days before deadline
            if days_to_deadline not in [10, 5, 2]:
                continue

            client = db.query(Client).filter(Client.id == filing.client_id).first()
            ca_firm = db.query(CAFirm).filter(CAFirm.id == filing.ca_firm_id).first()
            
            if not client or not ca_firm:
                continue

            # In a real scenario, you'd dynamically check what document categories are missing.
            missing_items = ["Pending Purchase Invoices", "Bank Statement"] 
            
            # Use CommunicationAgent to send the WhatsApp message
            CommunicationAgent.request_missing_document(
                client_wa_number=client.phone_whatsapp,
                firm_wa_id=ca_firm.whatsapp_number_assigned,
                missing_items=missing_items,
                deadline=filing.due_date.strftime("%d-%b-%Y")
            )
            logger.info(f"Sent reminder to {client.phone_whatsapp} for filing {filing.id}")

    except Exception as e:
        logger.error(f"Failed to send daily reminders: {str(e)}")
    finally:
        db.close()
