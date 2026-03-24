from fastapi import APIRouter

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.get("/")
async def list_documents():
    return {"status": "documents_stub"}
