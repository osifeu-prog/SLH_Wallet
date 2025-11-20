
from fastapi import APIRouter
router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/status")
def admin_status():
    return {"status": "ok", "message": "Admin endpoints placeholder"}
