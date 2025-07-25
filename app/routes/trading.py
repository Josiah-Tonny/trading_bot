from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List
from datetime import datetime

from app.database import get_db
from app.models.models import User
from app.services.signal_management import SignalManagementService
from app.services.user_session import UserSessionService
from app.services.payment_processor import PaymentProcessor
from app.auth import get_current_user

router = APIRouter()

@router.get("/signals/available")
async def get_available_signals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available signals for the current user"""
    signal_service = SignalManagementService(db)
    return signal_service.get_available_signals(current_user.id)

@router.post("/signals/change")
async def change_signal(
    symbol: str,
    payment_method: str = None,
    payment_details: Dict = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user's signal with payment handling"""
    signal_service = SignalManagementService(db)
    payment_processor = PaymentProcessor(db)
    
    # Check if change is allowed and get fee
    check_result = signal_service.can_change_signal(current_user.id)
    
    if not check_result["allowed"]:
        raise HTTPException(status_code=403, detail=check_result["reason"])
        
    # If fee required, process payment
    if check_result["fee"] > 0:
        if not payment_method or not payment_details:
            raise HTTPException(status_code=400, detail="Payment details required")
            
        payment_result = await payment_processor.process_signal_change_payment(
            current_user.id,
            payment_method,
            payment_details
        )
        
        if not payment_result["success"]:
            raise HTTPException(status_code=400, detail=payment_result["message"])
            
        return signal_service.change_signal(current_user.id, symbol, payment_confirmed=True)
        
    return signal_service.change_signal(current_user.id, symbol)

@router.post("/session/access-hours")
async def set_access_hours(
    start_time: str,
    end_time: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set user's preferred 4-hour access window"""
    session_service = UserSessionService(db)
    result = session_service.set_access_hours(current_user.id, start_time, end_time)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
        
    return result

@router.get("/session/status")
async def get_session_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's current session status and remaining time"""
    session_service = UserSessionService(db)
    access_check = session_service.check_user_access(current_user.id)
    
    if access_check["allowed"]:
        remaining = session_service.get_remaining_time(current_user.id)
        return {
            "allowed": True,
            "remaining_minutes": remaining["minutes"],
            "message": remaining["message"]
        }
        
    return {
        "allowed": False,
        "remaining_minutes": 0,
        "message": access_check["message"]
    }

@router.get("/signals/random")
async def get_random_signals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get random signals for free tier users"""
    signal_service = SignalManagementService(db)
    return signal_service.get_random_signals()
