from app import db
from datetime import datetime
import uuid

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    merchant_id = db.Column(db.String(36), db.ForeignKey('merchants.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='USD')
    card_id = db.Column(db.String(36), db.ForeignKey('cards.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, completed, failed, disputed
    transaction_type = db.Column(db.String(20), nullable=False, default='payment')  # payment, refund, chargeback
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Fraud detection results
    fraud_score = db.Column(db.Float, nullable=True)
    is_fraudulent = db.Column(db.Boolean, default=False)
    
    # Reference number for tracking
    reference_number = db.Column(db.String(20), unique=True, nullable=False)
    
    def __repr__(self):
        return f"Transaction('{self.reference_number}', '{self.amount}', '{self.status}')"


class Dispute(db.Model):
    __tablename__ = 'disputes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = db.Column(db.String(36), db.ForeignKey('transactions.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='open')  # open, resolved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship to get transaction details
    transaction = db.relationship('Transaction', backref='disputes', lazy=True)
    
    def __repr__(self):
        return f"Dispute('{self.id}', Transaction: '{self.transaction_id}', Status: '{self.status}')"