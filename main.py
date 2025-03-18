import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

from app import create_app
from app.models.user import User
from app.models.merchant import Merchant
from app.models.transaction import Transaction
from app.models.payment import Payment
from app.controllers.auth_controller import auth_bp
from app.controllers.payment_controller import payment_bp
from app.controllers.fraud_controller import fraud_bp
from app.controllers.admin_controller import admin_bp
from app.services.authentication import init_login_manager
from app.utils.init_data import initialize_demo_data
from config.database import db

# Create the Flask application
app = create_app()

# Initialize login manager
login_manager = init_login_manager(app)

# Register all blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(payment_bp, url_prefix='/api')
app.register_blueprint(fraud_bp, url_prefix='/api/fraud')
app.register_blueprint(admin_bp, url_prefix='/admin')

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Get recent transactions
    if current_user.role == 'admin':
        transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(10).all()
    else:
        transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).limit(10).all()
    
    # Calculate statistics
    total_transactions = len(transactions)
    total_amount = sum(t.amount for t in transactions) if transactions else 0
    success_count = sum(1 for t in transactions if t.status == 'completed') if transactions else 0
    success_rate = (success_count / total_transactions * 100) if total_transactions > 0 else 0
    
    stats = {
        'total_transactions': total_transactions,
        'total_amount': round(total_amount, 2),
        'currency': 'USD',
        'success_rate': round(success_rate, 2)
    }
    
    # Convert transaction objects to dictionaries with merchant name
    transaction_dicts = []
    for t in transactions:
        merchant = Merchant.query.get(t.merchant_id)
        transaction_dict = t.to_dict()
        transaction_dict['merchant_name'] = merchant.name if merchant else 'Unknown'
        transaction_dicts.append(transaction_dict)
    
    return render_template('dashboard.html', user=current_user, transactions=transaction_dicts, stats=stats)

@app.route('/transactions')
@login_required
def transactions():
    # Get all transactions
    if current_user.role == 'admin':
        transactions = Transaction.query.order_by(Transaction.created_at.desc()).all()
    else:
        transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).all()
    
    # Convert transaction objects to dictionaries with merchant name
    transaction_dicts = []
    for t in transactions:
        merchant = Merchant.query.get(t.merchant_id)
        transaction_dict = t.to_dict()
        transaction_dict['merchant_name'] = merchant.name if merchant else 'Unknown'
        transaction_dicts.append(transaction_dict)
    
    return render_template('transactions.html', user=current_user, transactions=transaction_dicts)

@app.route('/transactions/<transaction_id>')
@login_required
def transaction_detail(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Check if user has permission to view this transaction
    if current_user.role != 'admin' and transaction.user_id != current_user.id:
        flash('You do not have permission to view this transaction.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get associated data
    merchant = Merchant.query.get(transaction.merchant_id)
    payment = Payment.query.filter_by(transaction_id=transaction_id).first()
    
    # Convert to dictionary
    transaction_dict = transaction.to_dict()
    transaction_dict['merchant_name'] = merchant.name if merchant else 'Unknown'
    
    return render_template('transaction_detail.html', 
                          transaction=transaction_dict,
                          payment=payment)

@app.route('/transactions/new')
@login_required
def new_transaction():
    merchants = Merchant.query.all()
    return render_template('new_transaction.html', user=current_user, merchants=merchants)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        # Create all database tables
        db.create_all()
        
        # Initialize demo data if needed
        initialize_demo_data()
        
    # Run the application
    app.run(debug=True)