from app import db
from datetime import datetime
import uuid

class Merchant(db.Model):
    __tablename__ = 'merchants'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    business_name = db.Column(db.String(100), nullable=False)
    business_address = db.Column(db.String(200), nullable=False)
    business_phone = db.Column(db.String(20), nullable=False)
    business_email = db.Column(db.String(120), nullable=False)
    business_website = db.Column(db.String(100), nullable=True)
    business_description = db.Column(db.Text, nullable=True)
    
    # Merchant credentials for API
    api_key = db.Column(db.String(64), unique=True, nullable=False)
    api_secret = db.Column(db.String(128), nullable=False)
    
    # Merchant status
    is_verified = db.Column(db.Boolean, default=False)
    verification_date = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='merchant', lazy=True)
    
    def __repr__(self):
        return f"Merchant('{self.business_name}', '{self.business_email}')"