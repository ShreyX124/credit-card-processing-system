from app import db, bcrypt
from app.models.user import User, Card
from app.models.merchant import Merchant
from app.utils.encryption import encrypt_data
import os
import secrets
import uuid
from datetime import datetime

def create_initial_data():
    """
    Create initial demo data if database is empty
    """
    # Check if we already have users
    if User.query.count() > 0:
        return
    
    print("Creating initial demo data...")
    
    # Create admin user
    admin = User(
        id=str(uuid.uuid4()),
        email='admin@example.com',
        username='admin',
        first_name='Admin',
        last_name='User',
        role='admin',
        is_active=True
    )
    admin.set_password('admin123')
    db.session.add(admin)
    
    # Create merchant user
    merchant_user = User(
        id=str(uuid.uuid4()),
        email='merchant@example.com',
        username='merchant',
        first_name='Merchant',
        last_name='User',
        role='merchant',
        is_active=True
    )
    merchant_user.set_password('merchant123')
    db.session.add(merchant_user)
    
    # Create merchant profile
    merchant = Merchant(
        id=str(uuid.uuid4()),
        user_id=merchant_user.id,
        business_name='Example Store',
        business_address='123 Main St, Anytown, USA',
        business_phone='555-123-4567',