from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/health")
async def health(request: Request):
    return {"status": "ok"}
