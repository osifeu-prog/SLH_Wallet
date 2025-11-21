import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from ..blockchain_service import blockchain_service

logger = logging.getLogger("slh_wallet.wallet_router")

router = APIRouter(prefix="/api/wallet", tags=["wallet"])

@router.post("/register", response_model=schemas.WalletOut)
def register_wallet(
    payload: schemas.WalletRegisterIn,
    db: Session = Depends(get_db),
):
    try:
        # ✅ ולידציה - חובה Telegram ID
        if not payload.telegram_id or len(payload.telegram_id.strip()) == 0:
            raise HTTPException(status_code=400, detail="Telegram ID is required")
        
        # ✅ ולידציה - אורך כתובות
        if payload.bnb_address and len(payload.bnb_address) > 200:
            raise HTTPException(status_code=400, detail="BNB address too long")
        
        if payload.slh_address and len(payload.slh_address) > 200:
            raise HTTPException(status_code=400, detail="SLH address too long")
        
        if payload.bank_account_number and len(payload.bank_account_number) > 100:
            raise HTTPException(status_code=400, detail="Bank account number too long")

        # ✅ חיפוש או יצירת ארנק
        wallet = db.get(models.Wallet, payload.telegram_id)

        if not wallet:
            wallet = models.Wallet(telegram_id=payload.telegram_id)
            db.add(wallet)
            logger.info("Created new wallet for Telegram ID: %s", payload.telegram_id)
        else:
            logger.info("Updating existing wallet for Telegram ID: %s", payload.telegram_id)

        # ✅ עדכון כל השדות כולל החדשים
        update_fields = [
            'username', 'first_name', 'last_name', 
            'bnb_address', 'slh_address',
            'bank_account_number', 'bank_name', 'bank_branch'
        ]
        
        for field in update_fields:
            value = getattr(payload, field)
            if value is not None:
                setattr(wallet, field, value)

        db.commit()
        db.refresh(wallet)
        
        logger.info("Wallet saved successfully for Telegram ID: %s", payload.telegram_id)
        return wallet
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error saving wallet for Telegram ID %s: %s", payload.telegram_id, str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error saving wallet")

@router.get("/by-telegram/{telegram_id}", response_model=schemas.WalletOut)
def get_wallet_by_telegram(
    telegram_id: str,
    db: Session = Depends(get_db),
):
    if not telegram_id or len(telegram_id) > 50:
        raise HTTPException(status_code=400, detail="Invalid telegram ID")
        
    wallet = db.get(models.Wallet, telegram_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="User not found")
    return wallet

@router.get("/exists/{telegram_id}")
def check_wallet_exists(
    telegram_id: str,
    db: Session = Depends(get_db),
):
    if not telegram_id or len(telegram_id) > 50:
        return {"exists": False}
        
    wallet = db.get(models.Wallet, telegram_id)
    return {"exists": wallet is not None}

@router.get("/{telegram_id}/balances")
async def get_wallet_balances(
    telegram_id: str,
    db: Session = Depends(get_db),
):
    if not telegram_id or len(telegram_id) > 50:
        raise HTTPException(status_code=400, detail="Invalid telegram ID")
        
    wallet = db.get(models.Wallet, telegram_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    bnb_address = wallet.bnb_address or ""
    slh_address = wallet.slh_address or wallet.bnb_address or ""
    
    try:
        balances = await blockchain_service.get_balances(bnb_address, slh_address)
        
        return {
            "telegram_id": telegram_id,
            "bnb_balance": balances["bnb"],
            "slh_balance": balances["slh"],
            "bnb_address": bnb_address,
            "slh_address": slh_address,
            "success": True
        }
    except Exception as e:
        logger.error("Error getting balances for %s: %s", telegram_id, e)
        raise HTTPException(status_code=500, detail="Error fetching blockchain data")

@router.post("/upload-transfer-proof")
async def upload_transfer_proof(
    file: UploadFile = File(...),
    telegram_id: str = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    # ✅ בדיקה שהמשתמש קיים
    wallet = db.get(models.Wallet, telegram_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    try:
        # ✅ כאן תוסיף לוגיקה אמיתית לשמירת הקובץ
        # לדוגמה: שמירה ב-Amazon S3 או בשרת קבצים
        file_location = f"transfer_proofs/{telegram_id}_{file.filename}"
        
        return {
            "filename": file.filename,
            "telegram_id": telegram_id,
            "description": description,
            "status": "uploaded",
            "message": "File uploaded successfully - under review"
        }
    except Exception as e:
        logger.error("Error uploading file for %s: %s", telegram_id, e)
        raise HTTPException(status_code=500, detail="Error uploading file")

@router.get("/{telegram_id}/details")
def get_wallet_details(
    telegram_id: str,
    db: Session = Depends(get_db),
):
    """✅ endpoint חדש - מחזיר את כל פרטי הארנק"""
    if not telegram_id or len(telegram_id) > 50:
        raise HTTPException(status_code=400, detail="Invalid telegram ID")
        
    wallet = db.get(models.Wallet, telegram_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    return {
        "wallet": wallet,
        "has_metamask": bool(wallet.bnb_address),
        "has_bank_info": bool(wallet.bank_account_number),
        "registration_date": wallet.created_at
    }
