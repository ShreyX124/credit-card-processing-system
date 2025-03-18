from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.models.user import User
from app.models.merchant import Merchant
from app.models.transaction import Transaction
from app.services.security import check_admin_permissions
from app.utils.logging import log_activity
from config.database import get_db
from datetime import datetime, timedelta

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(check_admin_permissions)]
)

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_data(db: Session = Depends(get_db)):
    """
    Get admin dashboard data
    """
    now = datetime.utcnow()
    one_day_ago = now - timedelta(days=1)
    one_week_ago = now - timedelta(days=7)
    
    # Get transaction statistics
    total_transactions = db.query(Transaction).count()
    transactions_today = db.query(Transaction).filter(Transaction.created_at >= one_day_ago).count()
    transactions_week = db.query(Transaction).filter(Transaction.created_at >= one_week_ago).count()
    
    # Get fraud statistics
    flagged_transactions = db.query(Transaction).filter(Transaction.status == "flagged_for_fraud").count()
    flagged_today = db.query(Transaction).filter(
        Transaction.status == "flagged_for_fraud",
        Transaction.created_at >= one_day_ago
    ).count()
    
    # Get user statistics
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    
    # Get merchant statistics
    total_merchants = db.query(Merchant).count()
    active_merchants = db.query(Merchant).filter(Merchant.is_active == True).count()
    
    return {
        "transactions": {
            "total": total_transactions,
            "today": transactions_today,
            "week": transactions_week
        },
        "fraud": {
            "total_flagged": flagged_transactions,
            "flagged_today": flagged_today,
            "percentage": (flagged_transactions / total_transactions * 100) if total_transactions > 0 else 0
        },
        "users": {
            "total": total_users,
            "active": active_users
        },
        "merchants": {
            "total": total_merchants,
            "active": active_merchants
        }
    }

@router.get("/users", response_model=List[Dict[str, Any]])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all users with pagination
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return [user.to_dict() for user in users]

@router.get("/merchants", response_model=List[Dict[str, Any]])
async def get_all_merchants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all merchants with pagination
    """
    merchants = db.query(Merchant).offset(skip).limit(limit).all()
    return [merchant.to_dict() for merchant in merchants]

@router.get("/transactions", response_model=List[Dict[str, Any]])
async def get_all_transactions(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db)
):
    """
    Get all transactions with filters and pagination
    """
    query = db.query(Transaction)
    
    if status:
        query = query.filter(Transaction.status == status)
    
    transactions = query.offset(skip).limit(limit).all()
    return [transaction.to_dict() for transaction in transactions]

@router.put("/users/{user_id}", response_model=Dict[str, Any])
async def update_user_status(
    user_id: int,
    status_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Update user status (active/inactive)
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    user.is_active = status_data.get("is_active", user.is_active)
    db.commit()
    
    log_activity("admin_user_update", f"User {user_id} status updated to {user.is_active}")
    
    return {"message": "User updated successfully", "user": user.to_dict()}

@router.put("/merchants/{merchant_id}", response_model=Dict[str, Any])
async def update_merchant_status(
    merchant_id: int,
    status_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Update merchant status (active/inactive)
    """
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant with ID {merchant_id} not found"
        )
    
    merchant.is_active = status_data.get("is_active", merchant.is_active)
    db.commit()
    
    log_activity("admin_merchant_update", f"Merchant {merchant_id} status updated to {merchant.is_active}")
    
    return {"message": "Merchant updated successfully", "merchant": merchant.to_dict()}

@router.get("/logs", response_model=List[Dict[str, Any]])
async def get_system_logs(
    skip: int = 0,
    limit: int = 100,
    action_type: str = None,
    start_date: datetime = None,
    end_date: datetime = None
):
    """
    Get system activity logs with filters
    """
    # This endpoint would typically retrieve logs from a database or log file
    # For this implementation, we'll return sample data
    logs = [
        {
            "id": 1,
            "timestamp": datetime.utcnow().isoformat(),
            "action": "user_login",
            "details": "User 123 logged in",
            "ip_address": "192.168.1.1"
        },
        {
            "id": 2,
            "timestamp": datetime.utcnow().isoformat(),
            "action": "transaction_created",
            "details": "Transaction 456 created",
            "ip_address": "192.168.1.2"
        }
    ]
    
    return logs