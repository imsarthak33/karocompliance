from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.get("/me")
async def get_me():
    return {"status": "auth_stub"}
