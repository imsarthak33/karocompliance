from fastapi import APIRouter, Depends  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from app.database import get_db  # type: ignore
from app.models.document import Document  # type: ignore

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.get("/")
async def list_documents(db: Session = Depends(get_db)):
    """Returns all documents from the database."""
    documents = db.query(Document).order_by(Document.created_at.desc()).all()
    return documents
