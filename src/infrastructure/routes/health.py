from fastapi import APIRouter

router = APIRouter(tags=["Status"])


@router.get("/health")
async def health_check():
    """Verifica que el servidor esté corriendo."""
    return {"status": "ok", "service": "LivePoll"}
