
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.models.transaction import Transaction
from app.services.fraud_detection import FraudDetectionService
from app.utils.logging import log_activity
from config.database import get_db
from datetime import datetime

router = APIRouter(
    prefix="/fraud",
    tags=["fraud"],
    responses={404: {"description": "Not found"}},
)

fraud_service = FraudDetectionService()

@router.post("/check", response_model=Dict[str, Any])
async def check_transaction(
    transaction_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Check a transaction for potential fraud
    """
    log_activity("fraud_check", f"Checking transaction for fraud: {transaction_data.get('id', 'new')}")
    
    # Run fraud detection algorithm
    result = fraud_service.detect_fraud(transaction_data)
    
    if result["is_fraud"]:
        # Update transaction status if it exists in the database
        if "id" in transaction_data:
            transaction = db.query(Transaction).filter(Transaction.id == transaction_data["id"]).first()
            if transaction:
                transaction.status = "flagged_for_fraud"
                transaction.updated_at = datetime.utcnow()
                db.commit()
        
        log_activity("fraud_detected", f"Fraud detected in transaction: {transaction_data.get('id', 'new')}")
    
    return result

@router.get("/flagged", response_model=List[Dict[str, Any]])
async def get_flagged_transactions(
    db: Session = Depends(get_db)
):
    """
    Get all transactions flagged for fraud
    """
    transactions = db.query(Transaction).filter(Transaction.status == "flagged_for_fraud").all()
    return [transaction.to_dict() for transaction in transactions]

@router.post("/{transaction_id}/review", response_model=Dict[str, Any])
async def review_transaction(
    transaction_id: int,
    review_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Review a flagged transaction and update its status
    """
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID {transaction_id} not found"
        )
    
    # Update transaction status based on review
    new_status = review_data.get("status", "flagged_for_fraud")
    transaction.status = new_status
    transaction.updated_at = datetime.utcnow()
    db.commit()
    
    log_activity("fraud_review", f"Transaction {transaction_id} reviewed. New status: {new_status}")
    
    return {"message": "Transaction updated successfully", "transaction": transaction.to_dict()}

@router.get("/rules", response_model=List[Dict[str, Any]])
async def get_fraud_rules():
    """
    Get all fraud detection rules
    """
    return fraud_service.get_rules()

@router.post("/rules", response_model=Dict[str, Any])
async def add_fraud_rule(rule_data: Dict[str, Any]):
    """
    Add a new fraud detection rule
    """
    result = fraud_service.add_rule(rule_data)
    log_activity("fraud_rule_added", f"New fraud rule added: {rule_data.get('name')}")
    return result

@router.delete("/rules/{rule_id}", response_model=Dict[str, Any])
async def delete_fraud_rule(rule_id: str):
    """
    Delete a fraud detection rule
    """
    result = fraud_service.delete_rule(rule_id)
    log_activity("fraud_rule_deleted", f"Fraud rule deleted: {rule_id}")
    return result