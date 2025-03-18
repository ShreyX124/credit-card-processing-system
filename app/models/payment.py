from datetime import datetime
from config.database import db
from app.utils.encryption import encrypt_data, decrypt_data
import uuid

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = db.Column(db.String(36), db.ForeignKey('transactions.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='USD')
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, completed, failed, refunded
    payment_method = db.Column(db.String(50), nullable=False)
    card_number_encrypted = db.Column(db.Text, nullable=True)
    card_expiry_encrypted = db.Column(db.Text, nullable=True)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    refund_id = db.Column(db.String(36), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    transaction = db.relationship('Transaction', backref=db.backref('payments', lazy=True))
    
    def __init__(self, transaction_id, amount, payment_method, card_number=None, card_expiry=None, currency='USD'):
        self.transaction_id = transaction_id
        self.amount = amount
        self.currency = currency
        self.payment_method = payment_method
        
        # Encrypt sensitive card data if provided
        if card_number:
            self.set_card_number(card_number)
        if card_expiry:
            self.set_card_expiry(card_expiry)
    
    def set_card_number(self, card_number):
        """Encrypt and store the card number"""
        self.card_number_encrypted = encrypt_data(card_number)
    
    def get_card_number(self):
        """Decrypt and return the card number"""
        if self.card_number_encrypted:
            return decrypt_data(self.card_number_encrypted)
        return None
    
    def set_card_expiry(self, card_expiry):
        """Encrypt and store the card expiry date"""
        self.card_expiry_encrypted = encrypt_data(card_expiry)
    
    def get_card_expiry(self):
        """Decrypt and return the card expiry date"""
        if self.card_expiry_encrypted:
            return decrypt_data(self.card_expiry_encrypted)
        return None
    
    def update_status(self, new_status):
        """Update payment status and last_updated timestamp"""
        self.status = new_status
        self.last_updated = datetime.utcnow()
        
    def process_refund(self, refund_amount=None, notes=None):
        """Process a refund for this payment"""
        # Only allow refunds for completed payments
        if self.status != 'completed':
            return False, f"Cannot refund payment with status: {self.status}"
        
        # If no refund amount specified, refund the full amount
        refund_amount = refund_amount if refund_amount else self.amount
        
        # Don't allow refunding more than the original payment
        if refund_amount > self.amount:
            return False, "Refund amount cannot exceed original payment amount"
        
        # Generate a refund ID and update status
        self.refund_id = str(uuid.uuid4())
        self.status = 'refunded'
        self.last_updated = datetime.utcnow()
        
        if notes:
            self.notes = notes
            
        return True, {"refund_id": self.refund_id, "amount": refund_amount}
    
    def to_dict(self):
        """Convert payment object to dictionary"""
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status,
            'payment_method': self.payment_method,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'refund_id': self.refund_id
        }