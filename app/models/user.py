from app import db, login_manager, bcrypt
from flask_login import UserMixin
from datetime import datetime
import uuid

@login_manager.user_loader 
def load_user(user_id):
    return User.query.get(user_id)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer')  # customer, merchant, admin
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    cards = db.relationship('Card', backref='user', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_merchant(self):
        return self.role == 'merchant'
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role}')"


class Card(db.Model):
    __tablename__ = 'cards'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    card_number_hash = db.Column(db.String(128), nullable=False)
    card_holder_name = db.Column(db.String(100), nullable=False)
    expiry_month = db.Column(db.Integer, nullable=False)
    expiry_year = db.Column(db.Integer, nullable=False)
    card_type = db.Column(db.String(20), nullable=False)  # visa, mastercard, etc.
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Store the last 4 digits for display purposes
    last_four = db.Column(db.String(4), nullable=False)
    
    def __repr__(self):
        return f"Card('{self.card_type}', '****{self.last_four}', '{self.card_holder_name}')"