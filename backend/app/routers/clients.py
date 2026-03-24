from fastapi import APIRouter

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.get("/")
async def list_clients():
    return {"status": "clients_stub"}
