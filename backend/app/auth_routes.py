
from fastapi import APIRouter
router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/register")
def register_user():
    return {"status": "todo", "message": "Auth system to be implemented"}

@router.post("/login")
def login_user():
    return {"status": "todo", "message": "Auth system to be implemented"}
