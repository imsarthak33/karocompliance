from fastapi import APIRouter, Depends  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from app.database import get_db  # type: ignore
from app.models.client import Client  # type: ignore

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.get("/")
async def list_clients(db: Session = Depends(get_db)):
    """Returns all clients from the database."""
    clients = db.query(Client).all()
    return clients
